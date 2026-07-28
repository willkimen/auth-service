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
    Registers a new user account using the provided email address
    and password.

    The email address must be valid and not already associated with
    an existing account. The password must satisfy the applicable
    password policy before the user account is created. The
    resulting user data is returned as a public representation that
    excludes sensitive credentials.

    Attributes:
        `hasher` (HasherPort):
            - Port responsible for securely hashing the user's
              password before it is stored.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to register the user.
    """

    def __init__(self, hasher: HasherPort, uow: UnitOfWorkPort):
        self.hasher = hasher
        self.uow = uow

    async def execute(self, email: str, raw_password: str) -> UserPublicDTO:
        """
        Registers a new user account after validating the provided
        email address and password.

        The email address must be valid and available for registration,
        and the password must satisfy the password policy. The password
        is securely hashed before the new user account is persisted.
        The resulting user data is returned as a public representation
        that does not expose sensitive authentication credentials.

        Args:
            `email` (str):
                - Email address to be associated with the new user
                  account.
            `raw_password` (str):
                - Plain-text password provided by the user. It is
                  validated against the password policy and securely
                  hashed before being persisted.

        Returns:
            `UserPublicDTO`:
                - Public representation of the newly registered user,
                  excluding sensitive authentication credentials.

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
