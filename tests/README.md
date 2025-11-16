# HomeSeer MCP Test Suite

Unit and integration tests for the HomeSeer MCP Server.

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

Run with coverage:
```bash
pytest tests/ --cov=server --cov=config --cov-report=html
```
