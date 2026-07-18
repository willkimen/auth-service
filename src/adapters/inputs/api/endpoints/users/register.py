from adapters.inputs.api.dependencies.use_cases import RegisterUseCaseDep
from adapters.inputs.api.routers import users_router
from adapters.inputs.api.schemas import Credentials, UserPublic


@users_router.post('/register', response_model=UserPublic)
async def register(
    body: Credentials,
    use_case: RegisterUseCaseDep,
) -> UserPublic:
    """
    Registers a new user account.

    This endpoint:
        - Receives user credentials.
        - Delegates the registration workflow to the application layer.
        - Returns the newly created user's public information.

    Args:
        `body` (`Credentials`):
            - User registration credentials containing email and password.
        `use_case` (`RegisterUseCaseDep`):
            - Injected application use case responsible for user
              registration.

    Returns:
        `UserPublic`:
            - Public-safe representation of the newly created user.

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
              (infrastructure layer).
    """

    user = await use_case.execute(
        body.email,
        body.password,
    )

    return UserPublic(
        public_id=user.public_id,
        email=user.email,
        email_verified=user.email_verified,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )
