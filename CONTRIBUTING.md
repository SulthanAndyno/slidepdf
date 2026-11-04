# Contributing to SlidePDF Studio

We welcome contributions from the community! Whether you are fixing bugs, improving documentation, or adding new features, your help is appreciated.

## Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/SulthanAndyno/slidepdf.git
   cd slidepdf
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Run the test suite:
   ```bash
   make test
   # or
   PYTHONPATH=src pytest -v
   ```

## Pull Request Guidelines

- Ensure all 16+ tests pass before submitting a PR.
- Add test coverage for any new features or bug fixes.
- Follow PEP 8 style conventions and keep type hints clean.
- Write meaningful commit messages.
