from domain.exceptions import InvalidPasswordError

_min_length_password = 8
_max_length_password = 128


class PasswordPolicy:
    """Defines password validation rules."""

    @staticmethod
    def validate(raw_password: str) -> None:
        """Validates a raw password against security rules.

        Enforces length and requires letter, number, special char,
        uppercase, and lowercase.

        Args:
            raw_password (str): Raw password.

        Raises:
            InvalidPasswordError
        """
        if raw_password is None or not raw_password.strip():
            raise InvalidPasswordError('password cannot be empty')

        if len(raw_password) < _min_length_password:
            raise InvalidPasswordError('password too short')

        if len(raw_password) > _max_length_password:
            raise InvalidPasswordError('password too long')

        if not any(c.isalpha() for c in raw_password):
            raise InvalidPasswordError(
                'password must contain at least one letter'
            )

        if not any(c.isdigit() for c in raw_password):
            raise InvalidPasswordError(
                'password must contain at least one number'
            )

        if not any(not c.isalnum() for c in raw_password):
            raise InvalidPasswordError(
                'password must contain at least one special character'
            )

        if not any(c.isupper() for c in raw_password):
            raise InvalidPasswordError(
                'password must contain at least one uppercase character'
            )

        if not any(c.islower() for c in raw_password):
            raise InvalidPasswordError(
                'password must contain at least one lowercase character'
            )
