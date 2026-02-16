#!/usr/bin/env bash

################################################################################
#                                                                              #
#              RHINOMETRIC v2.3.0 - Test Suite Runner                         #
#                                                                              #
#  Ejecuta la suite completa de tests con reportes HTML/JSON                  #
#                                                                              #
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/tests/results"

# Colors
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[0;33m'
COLOR_CYAN='\033[0;36m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_CYAN}"
cat << "EOF"
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║            RHINOMETRIC v2.3.0 - AUTOMATED TEST SUITE                  ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${COLOR_RESET}"

# Check pytest installed
if ! command -v pytest &>/dev/null; then
    echo -e "${COLOR_RED}ERROR: pytest not installed${COLOR_RESET}"
    echo "Install with: pip install -r requirements-tests.txt"
    exit 1
fi

# Create results directory
mkdir -p "${RESULTS_DIR}/logs"

# Run tests
echo -e "${COLOR_CYAN}Running test suite...${COLOR_RESET}"
echo ""

pytest \
    -v \
    --maxfail=5 \
    --tb=short \
    --disable-warnings \
    --cov=. \
    --cov-report=html:tests/results/coverage-html \
    --cov-report=term-missing \
    --cov-report=json:tests/results/coverage.json \
    --html=tests/results/pytest-report.html \
    --self-contained-html \
    --junitxml=tests/results/junit.xml \
    tests/

EXIT_CODE=$?

# Generate summary
echo ""
echo -e "${COLOR_CYAN}Generating summary...${COLOR_RESET}"

python3 << 'PYTHON_SCRIPT'
import json
import sys
from pathlib import Path
from datetime import datetime

results_dir = Path("tests/results")

# Load coverage data
try:
    with open(results_dir / "coverage.json") as f:
        coverage_data = json.load(f)
    
    total_coverage = coverage_data["totals"]["percent_covered"]
except:
    total_coverage = 0.0

# Create summary
summary = f"""
{'='*70}
RHINOMETRIC v2.3.0 - TEST SUITE SUMMARY
{'='*70}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Coverage: {total_coverage:.2f}%
Status: {'✅ READY FOR PRODUCTION' if total_coverage >= 80 else '⚠️  NEEDS MORE COVERAGE'}

Reports generated:
  • HTML Report:    tests/results/pytest-report.html
  • Coverage HTML:  tests/results/coverage-html/index.html
  • Coverage JSON:  tests/results/coverage.json
  • JUnit XML:      tests/results/junit.xml
  • Logs:           tests/results/logs/

{'='*70}
"""

print(summary)

# Save summary
with open(results_dir / "summary.txt", "w") as f:
    f.write(summary)

sys.exit(0 if total_coverage >= 80 else 1)
PYTHON_SCRIPT

SUMMARY_EXIT=$?

# Final message
echo ""
if [[ $EXIT_CODE -eq 0 ]] && [[ $SUMMARY_EXIT -eq 0 ]]; then
    echo -e "${COLOR_GREEN}✓ ALL TESTS PASSED - COVERAGE ≥ 80%${COLOR_RESET}"
    echo ""
    echo "View reports:"
    echo "  HTML: file://${RESULTS_DIR}/pytest-report.html"
    echo "  Coverage: file://${RESULTS_DIR}/coverage-html/index.html"
else
    echo -e "${COLOR_YELLOW}⚠  SOME TESTS FAILED OR LOW COVERAGE${COLOR_RESET}"
    echo "Check: ${RESULTS_DIR}/pytest-report.html"
fi

exit $EXIT_CODE
