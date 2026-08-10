from auth_service.adapters.inputs.api.dependencies.use_cases import (
    RegisterUseCaseDep,
)
from auth_service.adapters.inputs.api.docs.user_error_responses import (
    register_responses,
)
from auth_service.adapters.inputs.api.routers import users_router
from auth_service.adapters.inputs.api.schemas import (
    CredentialsBodyRequest,
    UserPublicBodyResponse,
)


@users_router.post(
    '/register',
    response_model=UserPublicBodyResponse,
    summary='Register a new user',
    description="""
        Registers a new user account.
    """,
    responses=register_responses,
)
async def register(
    body: CredentialsBodyRequest,
    use_case: RegisterUseCaseDep,
) -> UserPublicBodyResponse:
    """
    Registers a new user account.

    This endpoint receives the user's registration credentials and
    initiates the account creation process using the provided email
    address and password.

    Args:
        `body` (`CredentialsBodyRequest`):
            - Request body containing the email address and password
              used to register the new account.
        `use_case` (`RegisterUseCaseDep`):
            - Injected application use case responsible for handling
              the user registration workflow.

    Returns:
        `UserPublicBodyResponse`:
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

    return UserPublicBodyResponse(
        public_id=user.public_id,
        email=user.email,
        email_verified=user.email_verified,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )
