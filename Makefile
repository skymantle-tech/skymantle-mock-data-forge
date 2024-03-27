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
	hatch run cov

lint_and_analysis:
	hatch run _ruff
	hatch run _bandit
	hatch run _black

build:
	hatch build

define HELP_TEXT
Usage: make <command>

Available commands:
  clean                	Cleans out virtual env and distribution folder
  install              	Installs virtual env and required packages
  unit_tests           	Run unit tests
  lint_and_analysis    	Runs ruff, bandit and black
  build					Builds package distribution 
endef