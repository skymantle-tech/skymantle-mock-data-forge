unitTests:
	hatch run cov

lintAndAnalysis:
	hatch run _ruff
	hatch run _bandit
	hatch run _black

build:
	rm -r dist
	hatch build

setup:
	pip install --upgrade pip
	pip install hatch 
	hatch env create default
