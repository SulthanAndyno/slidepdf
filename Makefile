# SlidePDF Studio Makefile

.PHONY: all run test build clean doctor install lint help

PYTHON = .venv/bin/python
PYTEST = .venv/bin/pytest

all: run

help:
	@echo "SlidePDF Studio Development Commands:"
	@echo "  make install    - Install dependencies into virtual environment"
	@echo "  make run        - Launch Desktop GUI application"
	@echo "  make doctor     - Run system engine health checks"
	@echo "  make test       - Run full pytest test suite"
	@echo "  make build      - Package standalone executable with PyInstaller"
	@echo "  make clean      - Clean temporary build and cache files"

install:
	bash install.sh

run:
	./run.sh

doctor:
	./run.sh doctor

test:
	PYTHONPATH=src $(PYTEST) -v

build:
	$(PYTHON) scripts/build_executable.py --onefile

clean:
	rm -rf build/ dist/ *.spec .pytest_cache/ htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf samples/*.pdf samples/combo_out/ samples/batch_out/
