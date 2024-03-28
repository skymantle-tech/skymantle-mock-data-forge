.PHONY: help clean install unit_tests lint_and_analysis build

help:
	$(info $(HELP_TEXT))
	@exit 0

clean:
	rm -rf .venv dist

install:
	pip install --upgrade pip
	pip install hatch 
	hatch env create default

unit_tests:
	hatch run pytest -v --cov-config=pyproject.toml --cov ./src

lint_and_analysis:
	hatch run ruff check .
	hatch run bandit -c pyproject.toml -r .
	hatch run black --check --diff .

build:
	hatch build

define HELP_TEXT
Usage: make <command>

Available commands:
  clean                 Cleans out virtual env and distribution folder
  install               Installs virtual env and required packages
  unit_tests            Run unit tests
  lint_and_analysis     Runs ruff, bandit and black
  build                 Builds package distribution 
endef