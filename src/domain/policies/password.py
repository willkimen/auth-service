from domain.exceptions import InvalidPasswordError, PasswordErrorCode

_min_length_password = 8
_max_length_password = 128


class PasswordPolicy:
    """Defines password validation rules."""

    @staticmethod
    def validate(raw_password: str) -> None:
        """
        Validates a raw password against security rules.

        Args:
            `raw_password` (str): Raw password.

        Raises:
            InvalidPasswordError:
                - If password is None or empty.
                - If password is shorter than the minimum allowed length.
                - If password is longer than the maximum allowed length.
                - If password does not contain at least one letter.
                - If password does not contain at least one number.
                - If password does not contain at least one special character.
                - If password does not contain at least
                    one uppercase character.
                - If password does not contain at least
                    one lowercase character.
        """
        if raw_password is None or not raw_password.strip():
            raise InvalidPasswordError(
                'password cannot be empty', PasswordErrorCode.PASSWORD_REQUIRED
            )

        if len(raw_password) < _min_length_password:
            raise InvalidPasswordError(
                'password too short', PasswordErrorCode.PASSWORD_TOO_SHORT
            )

        if len(raw_password) > _max_length_password:
            raise InvalidPasswordError(
                'password too long', PasswordErrorCode.PASSWORD_TOO_LONG
            )

        if not any(c.isalpha() for c in raw_password):
            raise InvalidPasswordError(
                'password must contain at least one letter',
                PasswordErrorCode.PASSWORD_MISSING_LETTER,
            )

        if not any(c.isdigit() for c in raw_password):
            raise InvalidPasswordError(
                'password must contain at least one number',
                PasswordErrorCode.PASSWORD_MISSING_NUMBER,
            )

        if not any(not c.isalnum() for c in raw_password):
            raise InvalidPasswordError(
                'password must contain at least one special character',
                PasswordErrorCode.PASSWORD_MISSING_SPECIAL,
            )

        if not any(c.isupper() for c in raw_password):
            raise InvalidPasswordError(
                'password must contain at least one uppercase character',
                PasswordErrorCode.PASSWORD_MISSING_UPPERCASE,
            )

        if not any(c.islower() for c in raw_password):
            raise InvalidPasswordError(
                'password must contain at least one lowercase character',
                PasswordErrorCode.PASSWORD_MISSING_LOWERCASE,
            )
