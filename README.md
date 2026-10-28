# auth-service

This documentation provides an overview of the project for anyone interested
in using, studying, or contributing to its development.

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

## Architecture

The architecture follows the Hexagonal Architecture approach, while also
incorporating some Domain-Driven Design (DDD) concepts.

The goal is to keep the application core as independent as possible from
frameworks, databases, and external services. This separation makes it easier
to replace infrastructure-specific components without changing the
application's business rules.

The project is organized into the following main layers:

* `domain`: contains the core business concepts, entities, and business rules.
* `application`: contains the application use cases, input and output ports,
  and application-level data structures.
* `adapters`: contains the implementations that connect the application to
  external interfaces and resources, such as the HTTP API, PostgreSQL, and
  RabbitMQ.
* `infrastructure`: contains technical components required to run the
  application, including configuration, database engine creation, and
  scheduled jobs.

### Infrastructure

The `infrastructure` package groups technical concerns that support the
application:

* `config`: loads application settings from environment variables and
  environment files.
* `database`: provides database infrastructure, including the SQLAlchemy
  engine.
* `scheduler`: registers and executes scheduled jobs, such as cleaning up
  expired verification codes and expired or revoked refresh tokens.

### Messaging and the Outbox Pattern

The application uses the Outbox Pattern to persist messages that need to be
published for asynchronous processing.

Messages are stored in PostgreSQL before they are published. A scheduled job
periodically invokes the `PublishEmailMessageUseCase`, which retrieves
pending messages and delegates publication through an output port. The
RabbitMQ publisher adapter implements this port and is responsible for
communicating with the broker.

This separates the application logic from the messaging technology: the use
case depends on an abstraction rather than directly on RabbitMQ.

The publisher sends email-related messages to a direct exchange named
`notifications`, using the routing key `email.send`. The consuming service
is responsible for declaring its queue and binding it to the exchange.

The `email-service` is intended to consume these messages and process the
corresponding email operations asynchronously.

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

### Referential Integrity

The database currently does not define foreign key constraints between
tables. This is an intentional design decision to keep the data model
simple and avoid introducing additional coupling between tables at this
stage of the project.

Referential integrity is enforced by the application, which validates
relationships between records when necessary, using identifiers such as
`user_public_id` and `sub`.

This approach keeps the schema flexible while the application is evolving.
Foreign key constraints may be introduced in the future if stronger
database-level referential integrity becomes necessary.

## Technologies

The main technologies used by the application are:

* APScheduler
* aio-pika
* bcrypt
* email-validator
* FastAPI
* PostgreSQL
* psycopg
* Pydantic Settings
* PyJWT
* RabbitMQ
* SQLAlchemy

For development and testing:

* Docker
* httpx
* pytest
* pytest-asyncio
* pytest-cov
* Ruff
* taskipy
* time-machine

## Setting Up Development and Running Tests

To set up the development environment, first install `uv` on your machine.

To install `uv`, follow the
[official installation instructions](https://docs.astral.sh/uv/getting-started/installation/).
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

## Running Tests — Starting the Test Containers

For integration tests involving the database, I chose not to use
`testcontainers`.

Instead of creating and destroying containers every time the tests are run,
the project uses dedicated Docker containers for the test PostgreSQL database
and RabbitMQ.

The idea is to keep the process simpler and more efficient. The containers
remain available while you are working, and the tests are already prepared to
clean the database tables before each test.

To start the test containers, use the `Makefile`.

The `Makefile` configures the test PostgreSQL instance with the data,
credentials, ports, and other settings expected by the application. It also
provides a command to start the RabbitMQ container used for integration tests.

To start the test database:

```bash
make db-test-up
```

To start the RabbitMQ container:

```bash
make rabbitmq-test-up
```

Once PostgreSQL and RabbitMQ are available, you can run the tests normally.

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
