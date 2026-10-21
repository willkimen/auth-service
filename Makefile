.PHONY: db-test-up db-test-clean db-test-logs rabbitmq-test-up rabbitmq-test-clean

db-test-up:
	docker volume create test-auth
	docker run --name postgres_test \
		-e POSTGRES_USER=test \
		-e POSTGRES_PASSWORD=test \
		-e POSTGRES_DB=test-auth \
		-v test-auth:/var/lib/postgresql \
		-v $(PWD)/scripts/create_tables.sql:/docker-entrypoint-initdb.d/create_tables.sql \
		-p 5432:5432 \
		-d postgres:18-alpine

db-test-clean:
	docker stop postgres_test && docker rm -f postgres_test
	docker volume rm test-auth

db-test-logs:
	docker logs -f postgres_test

rabbitmq-test-up:
	docker volume create test-rabbitmq
	docker run --name rabbitmq_test \
		-e RABBITMQ_DEFAULT_USER=test \
		-e RABBITMQ_DEFAULT_PASS=test \
		-v test-rabbitmq:/var/lib/rabbitmq \
		-p 5672:5672 \
		-d rabbitmq:4-management-alpine

rabbitmq-test-clean:
	docker rm -f rabbitmq_test 2>/dev/null || true
	docker volume rm test-rabbitmq
