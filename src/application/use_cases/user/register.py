from application.dtos.user_dto import UserPublicDTO
from application.exceptions import EmailAlreadyUsedError
from application.ports.output import HasherPort, UserRepositoryPort
from domain.entities.user import User
from domain.entities.user_factory import create_new_user
from domain.policies.password import PasswordPolicy
from domain.value_objects.email import Email
from domain.value_objects.password import PasswordHash


class RegisterUserUseCase:
    """
    Application use case responsible for registering new users.

    This use case validates user credentials, ensures email uniqueness,
    hashes the password, persists the user, and returns a public-safe DTO.
    """

    def __init__(self, hasher: HasherPort, user_repo: UserRepositoryPort):
        self.hasher = hasher
        self.user_repo = user_repo

    async def execute(self, email: str, raw_password: str) -> UserPublicDTO:
        """
        Registers a new user in the system using a hashed password.

        The use case validates the email and password, verifies that
        the email is not already in use, hashes the password, creates
        the user entity, persists it, and returns a public-safe DTO.


        Raises:
            InvalidEmailError:
                - Raised when the email is invalid.
            InvalidPasswordError:
                - Raised when the password does not satisfy the
                  password policy.
            EmailAlreadyUsedError:
                - Raised when the email is already being used by another user.
            InfrastructureError:
                - If an unexpected failure occurs within an output adapter
                  (infrastructure layer)

        """
        email_vo: Email = Email(email)
        PasswordPolicy.validate(raw_password)

        # The email must not already be associated with another account.
        exists: bool = await self.user_repo.exists_by_email(email_vo.value)
        if exists is True:
            raise EmailAlreadyUsedError()

        hashed_password: str = self.hasher.hash(raw_password)
        password_hash_vo: PasswordHash = PasswordHash(hashed_password)

        user: User = create_new_user(email_vo, password_hash_vo)

        await self.user_repo.create(user)

        # Sensitive data such as password hashes must never be exposed.
        return UserPublicDTO.from_entity(user)
