# HomeSeer MCP Test Suite

Unit and integration tests for the HomeSeer MCP Server.

## Setup

Ensure you have the required testing dependencies installed:
```bash
pip install -r requirements.txt
```

This includes:
- `pytest` - Testing framework
- `pytest-cov` - Coverage plugin

## Running Tests

Run all tests:
```bash
pytest tests/
```

Run with verbose output:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_server.py -v
```

## Coverage Reports

### Generate Coverage Files

Run tests with coverage reporting:
```bash
pytest tests/ --cov=server --cov=config --cov-report=xml --cov-report=html --cov-report=term
```

This generates:
- `coverage.xml` - XML format for VS Code Coverage Gutters
- `htmlcov/` - HTML report for detailed browser viewing
- Terminal summary - Quick overview in console

### View Coverage in VS Code

The Coverage Gutters extension highlights covered/uncovered lines directly in the editor:

1. Run tests with coverage (command above)
2. Open a Python file (`server.py` or `config.py`)
3. Click "Watch" in the status bar, or use Command Palette: "Coverage Gutters: Display Coverage"
4. Covered lines show green, uncovered lines show red in the gutter

### View HTML Coverage Report

For detailed line-by-line analysis:
```bash
start htmlcov/index.html  # Windows
```