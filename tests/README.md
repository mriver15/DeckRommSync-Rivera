# DeckRommSync Test Suite

## Running Tests

### Install test dependencies:
```bash
pip install -r requirements.txt
```

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

### Run specific test file:
```bash
pytest tests/test_app.py
```

### Run specific test class:
```bash
pytest tests/test_app.py::TestAppImports
```

### Run specific test:
```bash
pytest tests/test_app.py::TestAppImports::test_no_django_import
```

## Test Structure

- `conftest.py` - Shared fixtures and configuration
- `test_app.py` - Flask application and route tests
- `test_database.py` - Database operation tests
- `test_romm_api.py` - RomM API helper tests

## Fixtures Available

- `app` - Flask test application
- `client` - Flask test client
- `temp_db` - Temporary test database
- `mock_romm_api` - Mock RomM API responses
- `sample_config_data` - Sample configuration data
