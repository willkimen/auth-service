# auth-service

This documentation is intended to give anyone using, studying, or continuing the
development of this project a general understanding of how it works.

## Overview

The `auth-service` is responsible for centralizing user authentication and
account management.

It handles the main parts of a user's account lifecycle, including:

* User registration using email and password.
* Email verification.
* Password reset when the user forgets their password.
* Password changes.
* Email changes.
* Authentication.
* Access token renewal.
* Refresh token revocation.
* Permanent account removal (hard delete).
* Account deactivation (soft delete), making the user inactive. This operation
is intended for administrators and must be performed directly in the database.

This project is a skeleton and a starting point. The goal is not to provide a
complete solution for every possible scenario, but to provide a structure that
can be studied, adapted, and expanded according to the needs of each project.

### Important decision about email delivery

The email delivery mechanism was not implemented directly in this service. The
idea is to avoid tying the project to a specific solution, since there are
several ways to implement this part.

For example, someone may prefer to:

* Call the API of an email delivery service directly.
* Use a messaging system such as Celery.
* Use a scheduler such as APScheduler.
* Create a separate service responsible for sending emails.
* Use another communication method, such as SMS.

Because of this, the `auth-service` does not decide how a message is actually
delivered. It only records the intention to send it.

For this purpose, the Outbox Pattern is used. The data required to send a
message is persisted in the database before the process responsible for
delivery is executed. This ensures that the intention to send the message is not
lost if an external service is unavailable or the delivery process fails.

A separate Go service was also created that consumes the Resend API
to send the emails.

You can implement your own solution or use this service as a reference:

[email-service](https://github.com/willkimen/email-service?utm_source=chatgpt.com)

## Architecture

The architecture follows the Hexagonal Architecture approach, while also using
some DDD concepts.

The goal is to keep the application core as independent as possible from
frameworks, databases, and external services. This makes it easier to replace
infrastructure-specific components without having to change the main business rules.

The project is mainly divided into the following layers:

* `domain`: contains the core business rules and concepts.
* `application`: contains the application use cases and coordinates the
execution of business rules.
* `adapters`: contains the implementations responsible for communicating with
external resources, such as databases and other services.

In addition to these layers, there are two other parts:

* `config`: centralizes the application's configuration.
* `scheduler`: responsible for creating scheduled tasks that automate routines
such as removing verification codes and expired or revoked refresh tokens.

## Business Rules

The rules below are the main business rules of the domain, but they do not
represent every rule implemented in the application.

### User

* Email addresses are normalized to lowercase before being stored.
* A user has two independent states: active/inactive and email verified/unverified.
* Changes to the user's state, email, or password update `updated_at`.
* A login records the user's last login time.

### Password

* Passwords must be between 8 and 128 characters long.
* Passwords must contain an uppercase letter, a lowercase letter, a number, and
a special character.
* Passwords are never stored as plain text; only their hash is stored.

### Verification Code

* Verification codes contain 6 numeric digits.
* A verification code has an expiration time.
* A code is considered active only while it has not been used and has not expired.
* A used code cannot be reused.
* Email change codes must contain the new email associated with the code.

## Database

The database currently contains the following main structures:

* `Users`
* `Verification Codes`
* `Refresh Tokens`
* `Messages` — used by the Outbox Pattern to store messages that need to be processed.

## Technologies

The main technologies used by the application are:

* APScheduler
* bcrypt
* email-validator
* FastAPI
* psycopg
* pydantic-settings
* PyJWT
* SQLAlchemy

For development and testing:

* httpx
* pytest
* pytest-asyncio
* pytest-cov
* ruff
* taskipy
* time-machine

## Setting Up Development and Running Tests

To set up the development environment, first install `uv` on your machine.

There are several ways to install `uv`. You can choose whichever method you prefer:

* Using `pipx`.
* Using `pip`.
* Using the official standalone installer.

After installing `uv`, go to the directory containing the `pyproject.toml` file
and run:

```bash
uv sync
```

`uv sync` creates and manages the project's virtual environment, usually in
`.venv`, and installs the dependencies defined by the project.

The idea here was not to create a Docker container specifically for the
development environment. Python and its dependencies are isolated in the
virtual environment managed by `uv`, while Docker is used to provide the external
services required by the application, mainly the PostgreSQL database used for testing.

You also need to have Docker installed and running on your machine.

### Development helper commands

The commands most commonly used during development are defined in `pyproject.toml`.

To run a task:

```bash
uv run task <task>
```

The main tasks are:

* `lint`: Checks the code for problems and potential style issues using Ruff.
* `pre_format`: Automatically fixes some of the issues found by Ruff before formatting.
* `format`: Automatically formats the code according to Ruff's rules.
* `run`: Starts the FastAPI server in development mode.
* `pre_test`: Runs linting and formatting before the tests, ensuring that the
code is formatted and free of basic issues.
* `test`: Runs the automated tests and generates the code coverage report.
* `post_test`: Generates an HTML version of the coverage report, allowing it to
be viewed in a browser.

## Running Tests — Starting the Test Container

For integration tests involving the database, I chose not to use `testcontainers`.

Instead of creating and destroying a container every time the tests are run, the
project uses a dedicated Docker container for the test PostgreSQL database.

The idea is to keep the process simpler and more efficient. The container remains
available while you are working, and the tests are already prepared to clean the
tables before each test.

To start the container, use the `Makefile`.

The `Makefile` configures the test PostgreSQL instance with the data,
credentials, ports, and other settings expected by the application.

To start the test database:

```bash
make db-test-up
```

Once PostgreSQL is available, you can run the tests normally.

## Running the Production Environment

The project also provides a Docker Compose configuration for running the application
and its PostgreSQL database as containers.

Unlike the test setup described above, this configuration is intended to run the
application in its production environment.

To start the application and PostgreSQL containers in the background, run:

```bash
docker compose up -d
```

The `-d` option runs the containers in detached mode, allowing them to continue
running in the background while you use the terminal.

After the containers are started, the application and its PostgreSQL database will
be running according to the configuration defined in the Docker Compose file.

To stop the containers, run:

```bash
docker compose down
```

## Endpoint Documentation and Bruno API

The endpoint documentation is provided by FastAPI itself.

To access it:

1. Start the development server.
2. Open the Swagger documentation provided by FastAPI.

In addition to Swagger, the endpoints are also prepared for manual testing using
Bruno.

The Bruno request files are included in the project and can be used to test the
main API flows without having to build each request manually.
