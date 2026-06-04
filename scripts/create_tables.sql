CREATE TABLE IF NOT EXISTS refresh_tokens (
    jti VARCHAR(255) PRIMARY KEY,
    sub UUID NOT NULL,
    exp TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
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

    last_login_at TIMESTAMPTZ NULL,

    CONSTRAINT chk_updated_at_after_created_at
        CHECK (updated_at >= created_at),

    CONSTRAINT chk_last_login_at_after_created_at
        CHECK (
            last_login_at IS NULL
            OR last_login_at >= created_at
        )
);
