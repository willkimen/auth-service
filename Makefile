.PHONY: db-up db-down db-logs

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

db-test-down:
	docker stop postgres_test && docker rm postgres_test
	docker volume rm test-auth

db-test-logs:
	docker logs -f postgres_test
