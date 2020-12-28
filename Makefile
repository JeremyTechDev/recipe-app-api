help:
	@echo "Command list:"
	@echo ""
	@echo "- start		- Start the server"
	@echo "- test		- Run unit tests and linting checks"
	@echo "- lint		- Check for linting errors"

start:
	docker-compose up

test:
	docker-compose run --rm app sh -c 'python manage.py test && flake8'

lint:
	docker-compose run --rm app sh -c 'flake8'

default: help