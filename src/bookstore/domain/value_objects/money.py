from decimal import Decimal
from typing import Union
from bookstore.domain.base import ValueObject

class Money(ValueObject):

    def __init__(self, amount: Union[int, float, Decimal, str]):

        if isinstance(amount, float):
            amount = str(amount)
        self._amount = Decimal(amount)    
        if self._amount < 0:
            raise ValueError("Money cannot be negative")

    @property
    def amount(self) ->Decimal:
       return self._amount

    def __add__(self,other: 'Money' ) -> 'Money':
        if not isinstance(other, Money):
            raise TypeError("Money can be adde to othr money instane")
        return Money(self.amount + other.amount)

    def __sub__(self, other: 'Money') -> 'Money':
        if not isinstance(other, Money):
            raise TypeError("Money can be subtrack to othr money instane")
        result = self.amount - other.amount
        if result < 0:
            raise ValueError("Money cannot be negative")
        return Money(result)

    
    def __lt__(self, other: 'Money') -> bool:
        return self.amount < other.amount

    def __gt__(self, other: 'Money') -> bool:
        
        return self.amount > other.amount

    def __eq__(self, other: object) -> bool:
        
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount

    def __str__(self) -> str:
        
        return f"{self.amount:,.2f} Toman"

    def __repr__(self) -> str:
        return f"Money({self.amount})"
             

               