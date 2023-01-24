.ONESHELL:
ENV_PREFIX=$(shell python -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")
USING_POETRY=$(shell grep "tool.poetry" pyproject.toml && echo "yes")
SRC_DIRECTORIES := chartparse/ tests/ scripts/

.PHONY: help
help:              ## Show the help.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep


.PHONY: show
show:              ## Show the current environment.
	@echo "Current environment:"
	@if [ "$(USING_POETRY)" ]; then poetry env info && exit; fi
	@echo "Running using $(ENV_PREFIX)"
	@$(ENV_PREFIX)python -V
	@$(ENV_PREFIX)python -m site

.PHONY: install
install:           ## Install the project in dev mode.
	@if [ "$(USING_POETRY)" ]; then poetry install && exit; fi
	@echo "Don't forget to run 'make virtualenv' if you got errors."
	$(ENV_PREFIX)pip install -e .[test]

.PHONY: doc
doc:              ## Clean generated docs and compile fresh ones.
	$(MAKE) -C docs/ clean
	$(MAKE) -C docs/ html

.PHONY: black
black:             ## Format code using black.
	$(ENV_PREFIX)black -l 99 $(SRC_DIRECTORIES)

.PHONY: blackcheck
blackcheck:        ## Check code format using black.
	$(ENV_PREFIX)black -l 99 --check $(SRC_DIRECTORIES)

.PHONY: isort
isort:             ## Format code using isort.
	$(ENV_PREFIX)isort --line-length 99 $(SRC_DIRECTORIES)

.PHONY: autoflake
autoflake:         ## Remove unused imports using autoflake.
	$(ENV_PREFIX)autoflake -ri $(SRC_DIRECTORIES)

.PHONY: autoflakeall
autoflakeall:         ## Remove all unused imports using autoflake.
	$(ENV_PREFIX)autoflake --remove-all-unused-imports -ri $(SRC_DIRECTORIES)

.PHONY: fmt
fmt: isort black autoflake  ## Format code using isort, black, and autoflake.

.PHONY: flake
flake:             ## Run pep8 linter.
	$(ENV_PREFIX)flake8 --extend-ignore=E731 --max-line-length 99 --rst-roles meth,class,attr $(SRC_DIRECTORIES)

.PHONY: lint
lint: flake blackcheck  ## Run pep8 linter and black.

.PHONY: mypy
mypy:              ## Run mypy type checker.
	$(ENV_PREFIX)mypy --ignore-missing-imports $(SRC_DIRECTORIES)

.PHONY: check
check: lint mypy   ## Run all linters and mypy.

.PHONY: cov
cov:               ## Run tests and produce coverage reports if successful.
	@if $(ENV_PREFIX)pytest -vv --cov-config .coveragerc --cov-report term-missing --cov=chartparse -l --tb=short --maxfail=1 tests/; \
	then \
		:; \
	else \
		exit $?; \
	fi
	$(ENV_PREFIX)coverage xml
	$(ENV_PREFIX)coverage html

.PHONY: test
test:              ## Run tests and generate coverage report.
	$(ENV_PREFIX)pytest -vv	-l --tb=short tests/

.PHONY: proofnofmt
proofnofmt: check cov  ## ("Proofread") Run all linters, mypy, and unit tests, without fmt.

.PHONY: proof
proof: fmt check cov  ## ("Proofread") Run all linters, mypy, and unit tests.

.PHONY: watch
watch:             ## Run tests on every change.
	ls **/**.py | entr $(ENV_PREFIX)pytest -s -vvv -l --tb=long tests/

.PHONY: clean
clean:             ## Clean unused files.
	@find ./ -name '*.pyc' -exec rm -f {} \;
	@find ./ -name '__pycache__' -exec rm -rf {} \;
	@find ./ -name 'Thumbs.db' -exec rm -f {} \;
	@find ./ -name '*~' -exec rm -f {} \;
	@rm -rf .cache
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf build
	@rm -rf dist
	@rm -rf *.egg-info
	@rm -rf htmlcov
	@rm -rf .tox/

.PHONY: virtualenv
virtualenv:        ## Create a virtual environment.
	@if [ "$(USING_POETRY)" ]; then poetry install && exit; fi
	@echo "creating virtualenv ..."
	@rm -rf .venv
	@python3 -m venv .venv
	@./.venv/bin/pip install -U pip
	@./.venv/bin/pip install -e .[test]
	@echo
	@echo "!!! Please run 'source .venv/bin/activate' to enable the environment !!!"

.PHONY: release
release:           ## Create a new tag for release.
	@echo "WARNING: This operation will create s version tag and push to github"
	@read -p "Version? (provide the next x.y.z semver) : " TAG
	@echo "$${TAG}" > chartparse/VERSION
	@$(ENV_PREFIX)gitchangelog > HISTORY.md
	@git add chartparse/VERSION HISTORY.md
	@git commit -m "release: version $${TAG} 🚀"
	@echo "creating git tag : $${TAG}"
	@git tag $${TAG}
	@git push -u origin HEAD --tags
	@echo "Github Actions will detect the new tag and release the new version."

.PHONY: switch-to-poetry
switch-to-poetry:  ## Switch to poetry package manager.
	@echo "Switching to poetry ..."
	@if ! poetry --version > /dev/null; then echo 'poetry is required, install from https://python-poetry.org/'; exit 1; fi
	@rm -rf .venv
	@poetry init --no-interaction --name=a_flask_test --author=rochacbruno
	@echo "" >> pyproject.toml
	@echo "[tool.poetry.scripts]" >> pyproject.toml
	@echo "chartparse = 'chartparse.__main__:main'" >> pyproject.toml
	@cat requirements.txt | while read in; do poetry add --no-interaction "$${in}"; done
	@cat requirements-test.txt | while read in; do poetry add --no-interaction "$${in}" --dev; done
	@poetry install --no-interaction
	@mkdir -p .github/backup
	@mv requirements* .github/backup
	@mv setup.py .github/backup
	@echo "You have switched to https://python-poetry.org/ package manager."
	@echo "Please run 'poetry shell' or 'poetry run chartparse'"

.PHONY: init
init:              ## Initialize the project based on an application template.
	@./.github/init.sh


# This project has been generated from rochacbruno/python-project-template
# __author__ = 'rochacbruno'
# __repo__ = https://github.com/rochacbruno/python-project-template
# __sponsor__ = https://github.com/sponsors/rochacbruno/
