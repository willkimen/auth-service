from application.dtos.user_dto import UserPublicDTO
from application.exceptions import EmailAlreadyUsedError
from application.ports.output import HasherPort, UnitOfWorkPort
from domain.entities.user import User
from domain.entities.user_factory import create_new_user
from domain.policies.password import PasswordPolicy
from domain.value_objects.email import Email
from domain.value_objects.password import PasswordHash


class RegisterUserUseCase:
    """
    Application use case responsible for registering new users.

    Attributes:
        `hasher` (HasherPort):
            - Port/Interface responsible for hashing raw passwords securely.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for coordinating atomic
              transactional operations across repositories.
    """

    def __init__(self, hasher: HasherPort, uow: UnitOfWorkPort):
        self.hasher = hasher
        self.uow = uow

    async def execute(self, email: str, raw_password: str) -> UserPublicDTO:
        """
        Registers a new user in the system using a hashed password.

        This method:
            - Validates user credentials.
            - Ensures email uniqueness.
            - Hashes the password.
            - Persists the user, and returns a public-safe DTO.

        Args:
            `email` (str):
                - User email address used to identify the account.
            `raw_password` (str):
                - The plain-text password provided by the user,
                  which will be validated and hashed before storage.

        Raises:
            `InvalidEmailError`:
                - Raised when the email is invalid.
            `InvalidPasswordError`:
                - Raised when the password does not satisfy the
                  password policy.
            `EmailAlreadyUsedError`:
                - Raised when the email is already being used by another user.
            `InfrastructureError`:
                - If an unexpected failure occurs within an output adapter
                  (infrastructure layer)
        """

        async with self.uow:
            email_vo: Email = Email(email)
            PasswordPolicy.validate(raw_password)

            # The email must not already be associated with another account.
            exists: bool = await self.uow.users.exists_by_email(email_vo.value)
            if exists is True:
                raise EmailAlreadyUsedError()

            hashed_password: str = self.hasher.hash(raw_password)
            password_hash_vo: PasswordHash = PasswordHash(hashed_password)

            user: User = create_new_user(email_vo, password_hash_vo)
            await self.uow.users.create(user)

            # Sensitive data such as password hashes must never be exposed.
            return UserPublicDTO.from_entity(user)
