PYTHON := python3
CONFIG := config.txt
MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
	--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

.PHONY: install run debug clean lint lint-strict

install:
	$(PYTHON) -m pip install --upgrade build flake8 mypy

run:
	$(PYTHON) a_maze_ing.py $(CONFIG)

debug:
	$(PYTHON) -m pdb a_maze_ing.py $(CONFIG)

clean:
	rm -rf build dist .mypy_cache .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -maxdepth 2 -type d -name '*.egg-info' -exec rm -rf {} +

lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . $(MYPY_FLAGS)

lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict
