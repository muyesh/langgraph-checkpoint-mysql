.PHONY: test test_watch lint format

######################
# TESTING AND COVERAGE
######################

start-mysql:
	docker compose -f tests/compose-mysql.yml up -V --force-recreate --wait

stop-mysql:
	docker compose -f tests/compose-mysql.yml down

test:
	make start-mysql; \
	poetry run pytest; \
	EXIT_CODE=$$?; \
	make stop-mysql; \
	exit $$EXIT_CODE

test_watch:
	make start-mysql; \
	poetry run ptw .; \
	EXIT_CODE=$$?; \
	make stop-mysql; \
	exit $$EXIT_CODE

######################
# LINTING AND FORMATTING
######################

# Define a variable for Python and notebook files.
PYTHON_FILES=.
MYPY_CACHE=.mypy_cache
lint format: PYTHON_FILES=.
lint_diff format_diff: PYTHON_FILES=$(shell git diff --name-only --relative --diff-filter=d main . | grep -E '\.py$$|\.ipynb$$')
lint_package: PYTHON_FILES=langgraph
lint_tests: PYTHON_FILES=tests
lint_tests: MYPY_CACHE=.mypy_cache_test

lint lint_diff lint_package lint_tests:
	poetry run ruff check .
	[ "$(PYTHON_FILES)" = "" ] || poetry run ruff format $(PYTHON_FILES) --diff
	[ "$(PYTHON_FILES)" = "" ] || poetry run ruff check --select I $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || mkdir -p $(MYPY_CACHE)
	[ "$(PYTHON_FILES)" = "" ] || poetry run mypy $(PYTHON_FILES) --cache-dir $(MYPY_CACHE)

format format_diff:
	poetry run ruff format $(PYTHON_FILES)
	poetry run ruff check --select I --fix $(PYTHON_FILES)
