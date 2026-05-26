# ruff: noqa: PLR6301
import bcrypt

from application.exceptions import InfrastructureError, InfrastructureErrorCode


class BcryptHasher:
    """Defines password hashing and verification operations."""

    def hash(self, raw_password: str) -> str:
        """Hashes a raw password into a secure representation.

        Args:
            `raw_password` (str):
                - The plain text password to be hashed.

        Returns:
            `str`:
                - The generated bcrypt hash decoded into a string.

        Raises:
            `InfrastructureError`:
                - If hashing algorithm or cryptographic library fails.
        """
        try:
            password_bytes = raw_password.encode('utf-8')
            hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
            return hashed_bytes.decode('utf-8')
        except Exception as e:
            raise InfrastructureError(
                message=(
                    'An unexpected cryptographic or data error occurred'
                    ' within the password hashing service.'
                ),
                code=InfrastructureErrorCode.PASSWORD_HASHER,
                cause=e,
            )

    def verify_password(self, raw_password: str, hashed_password: str) -> bool:
        """
        Verifies a raw password against an existing secure hash representation.

        Args:
            `raw_password` (str):
                - The plain text password provided during login.
            `hashed_password` (str):
                - The trusted hash retrieved from database.

        Returns:
            `bool`:
                - True if the password matches the hash, False otherwise.

        Raises:
            `InfrastructureError`:
                - If the verification process or cryptographic library fails.
        """
        try:
            password_bytes = raw_password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            raise InfrastructureError(
                message=f'Password verification failure. Original error: {e}',
                code=InfrastructureErrorCode.PASSWORD_HASHER,
                cause=e,
            )
