from fastapi import status

from adapters.inputs.api.dependencies.use_cases import LoginDep
from adapters.inputs.api.routers import auth_router
from adapters.inputs.api.schemas import (
    CredentialsBodyRequest,
    TokensBodyResponse,
)
from application.dtos.token_dto import PairTokensDTO


@auth_router.post(
    '/token/login',
    status_code=status.HTTP_200_OK,
    response_model=TokensBodyResponse,
)
async def login(
    body: CredentialsBodyRequest,
    use_case: LoginDep,
) -> TokensBodyResponse:
    """
    Authenticates a user using their email and password and returns
    an access token and a refresh token for the authenticated session.

    Args:
        `body` (`CredentialsBodyRequest`):
            - Request body containing the user's email address and password.
        `use_case` (`LoginDep`):
            - Injected application use case responsible for authenticating
              the user and generating the authentication token pair.

    Returns:
        `TokensBodyResponse`:
            - Response body containing the access and refresh tokens.

    Raises:
        `InvalidCredentialsError`:
            - If user does not exist or password is invalid.
        `InactiveUserError`:
            - If user account is inactive.
        `UnverifiedEmailError`:
            - If user email has not been verified.
        `InfrastructureError`:
            - If repository, hashing, or token generation fails.
    """
    tokens: PairTokensDTO = await use_case.execute(body.email, body.password)

    return TokensBodyResponse(
        access=tokens.access.token, refresh=tokens.refresh.token
    )
