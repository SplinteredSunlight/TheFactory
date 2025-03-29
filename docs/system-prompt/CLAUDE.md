# AI-Orchestration-Platform Development Guide

## Common Commands
- Setup: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- Run Tests: `pytest` (all), `pytest tests/test_file.py` (file), `pytest tests/test_file.py::TestClass::test_method` (specific)
- Coverage: `pytest --cov=src tests/`
- Test Markers: `pytest -m integration`, `-m auth`, `-m agent`, `-m task`, `-m error`, `-m dagger`
- Lint Python: `black src tests` (format), `isort src tests` (imports), `flake8 src tests`
- Type Check: `mypy src`
- Frontend: `cd src/frontend && npm test` (test), `npm run lint` (lint), `npm run format` (format)
- Start Services: `docker-compose up -d`
- Project Tools: `./task [status|complete|next|start]`, `./run_dagger_tests.sh`, `./show-progress.sh`

## Code Style Guide
- **Python**: PEP 8, black formatting, typed (mypy), snake_case for functions/vars, PascalCase for classes
- **TypeScript**: Prettier formatting, functional components, Redux Toolkit for state
- **Imports**: Use isort (Python), group by type (React, Material UI, local)
- **Documentation**: Triple-quotes docstrings for modules/classes/functions with parameter descriptions
- **Error Handling**: Use custom exceptions from `orchestrator/error_handling.py`, RetryHandler for retries
- **Testing**: pytest fixtures, React Testing Library, descriptive test names
- **APIs**: Consistent error response format with code, message, and details

## Project Structure
- Backend: Python (FastAPI, Pydantic), structured by domain
- Frontend: TypeScript/React with Material UI
- Agent System: Modular design with adapters for different agent types and standardized communication
- Dagger Integration: Workflow engine for containerized task execution
- Configuration: Layered system with default.yaml, env vars, and module-specific configs
- Git workflow: Format and lint before commit, descriptive commit messages