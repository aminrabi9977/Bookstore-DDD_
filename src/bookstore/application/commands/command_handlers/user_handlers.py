from datetime import datetime
import hashlib
import secrets
from typing import Optional
from bookstore.application.commands.user_commands import (RegisterUser,VerifyUser,CreateCustomer, ChangeSubscription,
    AddWalletBalance, UpdateUserProfile, ChangeUserPassword, RequestPasswordReset,ResetPassword,GenerateOTP)
from bookstore.application.commands.base import CommandResult
from bookstore.domain.aggregates.user import User
from bookstore.domain.aggregates.customer import Customer
from bookstore.domain.value_objects.money import Money
from bookstore.application.commands.command_handlers.base import CommandHandler, ValidationError, BusinessRuleViolation


class RegisterUserHandler(CommandHandler[RegisterUser]):
    async def handle(self, command: RegisterUser) -> CommandResult:
        try:
            async with self.uow:
                existing_user = await self.uow.users.get_by_email(command.email)
                if existing_user:
                    raise ValidationError("email already registere=d")
                existing_phone = await self.uow.users.get_by_phone(command.phone)
                if existing_phone:
                    raise ValidationError("phone number already registered")
                password_hash = hashlib.sha256(command.password.encode()).hexdigest()

                user = User(
                    email=command.email,
                    password_hash=password_hash,
                    phone=command.phone,
                    role=command.role
                )

                otp = secrets.randbelow(900000) + 100000  
                await self.uow.cache.store_otp(user.phone, str(otp))

                await self.uow.users.add(user)
                await self.uow.commit()

                await self.uow.sms.send_otp(user.phone, str(otp))
                return CommandResult(success=True,
                    message="user registered successfully. Please verify your phone.",
                    data={"user_id": str(user.id)}
                )

        except ValidationError as e:
            return CommandResult(success=False,
                message=str(e),
                error=str(e))

        except Exception as e:
            return CommandResult(
                success=False,
                message="failed to regster user",
                error=str(e)
            )


class VerifyUserHandler(CommandHandler[VerifyUser]):
    async def handle(self, command: VerifyUser) -> CommandResult:
        try:
            async with self.uow:
                user = await self.uow.users.get(command.user_id)
                if not user:
                    raise ValidationError("user not found")
                is_valid = await self.uow.cache.verify_otp(
                    user.phone,
                    command.otp)


                if not is_valid:
                    raise ValidationError("invalid otp")

                user.verify()
                await self.uow.users.update(user)
                await self.uow.commit()
                return CommandResult(
                    success=True,
                    message="user verified successfully")

        except ValidationError as e:
            return CommandResult(success=False,
                message=str(e),
                error=str(e))

        except Exception as e:
            return CommandResult(success=False,
                message="failed to verify user",
                error=str(e))




class CreateCustomerHandler(CommandHandler[CreateCustomer]):
    async def handle(self, command: CreateCustomer) -> CommandResult:
        try:
            async with self.uow:
                user = await self.uow.users.get(command.user_id)
                if not user:
                    raise ValidationError("user not found")

                existing = await self.uow.customers.get_by_user_id(command.user_id)
                if existing:
                    raise ValidationError("customer profile already exists")
                customer = Customer(
                    user_id=command.user_id,
                    subscription_type=command.subscription_type)

                await self.uow.customers.add(customer)
                await self.uow.commit()
                return CommandResult(success=True,
                    message="customer profile created successfully",
                    data={"customer_id": str(customer.id)})

        except ValidationError as e:
            return CommandResult(
                success=False,
                message=str(e),
                error=str(e))
        except Exception as e:
            return CommandResult(
                success=False,
                message="failed to create customer profile",
                error=str(e))



class ChangeSubscriptionHandler(CommandHandler[ChangeSubscription]):
    async def handle(self, command: ChangeSubscription) -> CommandResult:
        try:
            async with self.uow:
                customer = await self.uow.customers.get(command.customer_id)
                if not customer:
                    raise ValidationError("customer not found")
                customer.change_subscription(command.new_subscription)
                await self.uow.customers.update(customer)
                await self.uow.commit()
                return CommandResult(success=True,
                    message="subscription changed successfully")


        except ValidationError as e:
            return CommandResult(
                success=False,
                message=str(e),
                error=str(e))

        except Exception as e:
            return CommandResult(success=False,
                message="failed to change subscription",
                error=str(e))




class AddWalletBalanceHandler(CommandHandler[AddWalletBalance]):
    async def handle(self, command: AddWalletBalance) -> CommandResult:
        try:
            async with self.uow:
                customer = await self.uow.customers.get(command.customer_id)
                if not customer:
                    raise ValidationError("customer not fond")

                customer.credit_wallet(Money(command.amount))
                
                await self.uow.customers.update(customer)
                await self.uow.commit()
                return CommandResult(success=True,
                    message="wallet balance updated successfully",
                    data={"new_balance": float(customer.wallet_balance.amount)})

        except ValidationError as e:
            return CommandResult(
                success=False,
                message=str(e),
                error=str(e))

        except Exception as e:
            return CommandResult(
                success=False,
                message="Failed to add wallet balance",
                error=str(e))


class UpdateUserProfileHandler(CommandHandler[UpdateUserProfile]):
    async def handle(self, command: UpdateUserProfile) -> CommandResult:
        try:
            async with self.uow:
                user = await self.uow.users.get(command.user_id)
                if not user:
                    raise ValidationError("user not found")

                if command.email and command.email != user.email:
                    existing = await self.uow.users.get_by_email(command.email)
                    if existing:
                        raise ValidationError("email already in use")
                if command.phone and command.phone != user.phone:
                    existing = await self.uow.users.get_by_phone(command.phone)
                    if existing:
                        raise ValidationError("phone number already in use")

                if command.email:
                    user._email = command.email
                if command.phone:
                    user._phone = command.phone

                await self.uow.users.update(user)
                await self.uow.commit()
                return CommandResult(success=True,
                    message="profile updated successfully"
                )
        except ValidationError as e:
            return CommandResult(success=False,
                message=str(e),
                error=str(e))
        except Exception as e:
            return CommandResult(success=False,
                message="failed to update profile",
                error=str(e)
            )




class GenerateOTPHandler(CommandHandler[GenerateOTP]):
    async def handle(self, command: GenerateOTP) -> CommandResult:
        try:
            async with self.uow:
                allowed = await self.uow.cache.track_otp_requests(command.phone)
                if not allowed:
                    raise BusinessRuleViolation("many otp request")

                otp = secrets.randbelow(900000) + 100000  # 
                await self.uow.cache.store_otp(command.phone, str(otp))
                await self.uow.sms.send_otp(command.phone, str(otp))
                return CommandResult(
                    success=True,
                    message="otp sent succesfully")
        except BusinessRuleViolation as e:
            return CommandResult(
                success=False,
                message=str(e),
                error=str(e) )

        except Exception as e:
            return CommandResult(success=False,
                message="failed to generate otp",
                error=str(e))