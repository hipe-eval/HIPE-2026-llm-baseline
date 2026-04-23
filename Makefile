PYTHON ?= python3

.PHONY: install test
install:
	$(PYTHON) -m pip install -e .

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"
