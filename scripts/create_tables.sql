CREATE TABLE IF NOT EXISTS refresh_tokens (
    jti VARCHAR(255) PRIMARY KEY,
    sub UUID NOT NULL,
    exp TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMPTZ DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_refresh_tokens_sub ON refresh_tokens(sub);

CREATE TABLE IF NOT EXISTS users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    public_id UUID NOT NULL UNIQUE,

    email VARCHAR(320) NOT NULL UNIQUE,
    hash_password TEXT NOT NULL,

    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,

    last_login_at TIMESTAMPTZ DEFAULT NULL,

    CONSTRAINT chk_updated_at_after_created_at
        CHECK (updated_at >= created_at),

    CONSTRAINT chk_last_login_at_after_created_at
        CHECK (
            last_login_at IS NULL
            OR last_login_at >= created_at
        )
);

CREATE TYPE verification_code_type AS ENUM (
    'email_verification',
    'change_email',
    'change_password',
    'reset_password',
    'delete_account'
);

CREATE TABLE IF NOT EXISTS verification_codes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code varchar(32) NOT NULL,
    user_public_id UUID NOT NULL,
    type verification_code_type NOT NULL,

    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ DEFAULT NULL,

    payload JSONB DEFAULT NULL,


    CONSTRAINT chk_expires_at_after_created_at
        CHECK (
            expires_at >= created_at
        ),

    CONSTRAINT chk_used_at_after_created_at
        CHECK (
            used_at IS NULL OR
            used_at >= created_at
        )
);
CREATE INDEX idx_verification_code_user_id ON verification_codes(user_public_id);
CREATE INDEX idx_verification_code_code ON verification_codes(code);
