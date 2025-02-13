from fastapi import APIRouter, Depends, HTTPException, Request, Query
from typing import Optional, List
from uuid import UUID

from bookstore.interfaces.api.schemas import BookCreateRequest, BookUpdateRequest,BookResponse,PaginatedResponse
from bookstore.interfaces.api.middleware.authentication import get_current_user_id
from bookstore.application.commands.book_commands import CreateBook,UpdateBook,DeleteBook,AddBookUnits,RemoveBookUnits
from bookstore.infrastructure.persistence.database import get_session
from bookstore.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter()

@router.post("", response_model=BookResponse)
async def create_book(
    request: Request,
    book_data: BookCreateRequest,
    session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        user = await uow.users.get(user_id)
        if not user or user.role.value not in ["admin", "author"]:
            raise HTTPException(
                status_code=403,
                detail="nt authorized to create books"
            )

        command = CreateBook(
            title=book_data.title,
            isbn=book_data.isbn,
            price=book_data.price,
            author_id=book_data.author_id,
            genre_id=book_data.genre_id,
            description=book_data.description,
            total_units=book_data.total_units
        )
        
        result = await uow.message_bus.execute(command)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error
            )

        book = await uow.books.get(result.data["book_id"])
        return BookResponse.model_validate(book)

@router.get("", response_model=PaginatedResponse)
async def list_books(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    genre_id: Optional[UUID] = None,
    author_id: Optional[UUID] = None,
    session = Depends(get_session)
):
    async with SqlAlchemyUnitOfWork(session) as uow:
        filters = {}
        if genre_id:
            filters["genre_id"] = genre_id
        if author_id:
            filters["author_id"] = author_id

        skip = (page - 1) * size
        books = await uow.books.list(
            filters=filters,
            skip=skip,
            limit=size)
        total = len(await uow.books.list(filters=filters))
        return PaginatedResponse(
            items=[BookResponse.model_validate(book) for book in books],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )



@router.get("/search", response_model=PaginatedResponse)
async def search_books(query: str,page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    session = Depends(get_session)):
    async with SqlAlchemyUnitOfWork(session) as uow:
        skip = (page - 1) * size
        books = await uow.book_search.search(
            query=query,
            fields=["title", "description"],
            skip=skip,
            limit=size)
        
        total = len(await uow.book_search.search(
            query=query,
            fields=["title", "description"]))
        
        return PaginatedResponse(
            items=[BookResponse.model_validate(book) for book in books],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size)



@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: UUID,
    session = Depends(get_session)):
    async with SqlAlchemyUnitOfWork(session) as uow:
        book = await uow.books.get(book_id)
        if not book:
            raise HTTPException(
                status_code=404,
                detail="book not found"
            )
        return BookResponse.model_validate(book)


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    request: Request,
    book_id: UUID,
    book_data: BookUpdateRequest,
    session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        user = await uow.users.get(user_id)
        book = await uow.books.get(book_id)
        if not user or not book:
            raise HTTPException(
                status_code=404,
                detail="book not found"
            )
            
        if user.role.value != "admin" and book.author_id != user_id:
            raise HTTPException(status_code=403,
                detail="not authorized to update this book")

        command = UpdateBook(
            id=book_id,
            title=book_data.title,
            price=book_data.price,
            description=book_data.description,
            genre_id=book_data.genre_id)
        
        result = await uow.message_bus.execute(command)
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error)

        book = await uow.books.get(book_id)
        return BookResponse.model_validate(book)



@router.delete("/{book_id}")
async def delete_book(
    request: Request,
    book_id: UUID,
    session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        user = await uow.users.get(user_id)
        if not user or user.role.value != "admin":
            raise HTTPException(
                status_code=403,
                detail="not authorized to delete books")

        command = DeleteBook(id=book_id)
        result = await uow.message_bus.execute(command)
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error)

        return {"message": "Book deleted successfully"}



@router.post("/{book_id}/units/add")
async def add_book_units(
    request: Request,
    book_id: UUID,
    count: int = Query(..., gt=0),
    session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        user = await uow.users.get(user_id)
        if not user or user.role.value != "admin":
            raise HTTPException(
                status_code=403,
                detail="Not authorized to modify inventory")

        command = AddBookUnits(
            id=book_id,
            count=count)
        result = await uow.message_bus.execute(command)
        
        if not result.success:
            raise HTTPException(status_code=400,
                detail=result.error)

        return {"message": f"added {count} units successfully"}


@router.post("/{book_id}/units/remove")
async def remove_book_units(
    request: Request,
    book_id: UUID,
    count: int = Query(..., gt=0),
    session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        user = await uow.users.get(user_id)
        if not user or user.role.value != "admin":
            raise HTTPException(status_code=403,
                detail="not authorized to modify inventory"
            )

        command = RemoveBookUnits(
            id=book_id,
            count=count
        )
        result = await uow.message_bus.execute(command)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error
            )

        return {"message": f"Removed {count} units successfully"}