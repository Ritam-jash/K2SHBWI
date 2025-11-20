# CI-Friendly Test Suite

## Overview

The `comprehensive_test_suite_ci.py` is designed specifically for CI/CD environments where test files don't exist. It automatically creates all required test assets on-the-fly.

## Key Features

✅ **No External Dependencies** - Creates all test files automatically  
✅ **Temporary Directories** - Uses system temp directories, cleans up after  
✅ **CI-Safe** - No hardcoded paths or file requirements  
✅ **Same Test Coverage** - Tests all 19 test cases from comprehensive suite  

## Differences from `comprehensive_test_suite.py`

| Feature | `comprehensive_test_suite.py` | `comprehensive_test_suite_ci.py` |
|---------|------------------------------|----------------------------------|
| Test Image | Requires `test_image.png` | Creates on-the-fly |
| K2SH File | Requires `test_output_click.k2sh` | Creates on-the-fly |
| Batch Input | Requires `batch_input/` directory | Creates on-the-fly |
| Logging | Full TestLogger support | Optional (graceful fallback) |
| Cleanup | Leaves test files | Auto-cleans temp files |
| Use Case | Local development | CI/CD environments |

## Usage

### In CI/CD (GitHub Actions)
```yaml
- name: Run CI-friendly test suite
  run:
    export PYTHONPATH=.
    python tests/comprehensive_test_suite_ci.py
```

### Locally
```bash
# From project root
python tests/comprehensive_test_suite_ci.py
```

## Test Coverage

The CI-friendly suite tests all 19 test cases:

**Phase 3: Commands (7 tests)**
- Create Command
- Create with Metadata
- Info Command
- Validate Command
- Decode Command
- Batch Command
- Encode Command

**Phase 4: Converters (4 tests)**
- Convert to HTML
- Convert to PDF
- Convert to PPTX
- All Conversion Formats

**Phase 5: Viewers (1 test)**
- View Command Help

**Phase 6: Testing & Validation (4 tests)**
- All Commands Have Help
- Create Multiple Files
- Validate All Outputs
- Verbose Output

**Phase 7: Documentation (3 tests)**
- CLI Version Display
- Main Help
- Command Examples

## Output

- **Console**: Real-time test progress and summary
- **TEST_RESULTS.json**: Detailed JSON results file
- **Logs** (optional): If TestLogger is available

## Requirements

- Python 3.10+
- Pillow (PIL) - for generating test images
- All K2SHBWI dependencies (from `requirements.txt`)

## Notes

- Test files are created in a temporary directory (system temp)
- All temporary files are automatically cleaned up after tests
- If TestLogger is unavailable, tests continue without logging
- Exit code: 0 if all tests pass, 1 if any fail

