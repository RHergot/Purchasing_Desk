#!/usr/bin/env bash
# setup.sh — Automated setup for Purchasing Desk
# Usage: bash setup.sh

set -euo pipefail

echo "=== Purchasing Desk Setup ==="

# 1. Python version check
PYTHON="python3"
if ! command -v $PYTHON &>/dev/null; then
    PYTHON="python"
fi

PYVER=$($PYTHON --version 2>&1 | grep -oP '\d+\.\d+')
echo "Python version: $PYVER"

# 2. Virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv venv
fi

echo "Activating venv..."
source venv/bin/activate

# 3. Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Check wkhtmltopdf
if ! command -v wkhtmltopdf &>/dev/null; then
    echo ""
    echo "WARNING: wkhtmltopdf not found in PATH."
    echo "Install it for PDF generation:"
    echo "  Debian/Ubuntu: sudo apt-get install wkhtmltopdf"
    echo "  macOS:         brew install wkhtmltopdf"
    echo "  Windows:       https://wkhtmltopdf.org/downloads.html"
    echo ""
fi

# 5. Environment file
if [ ! -f ".env" ]; then
    echo "Creating .env template..."
    cat > .env << 'EOF'
DB_USER=postgres
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=purchasing_desk
# Optional company info for PDFs:
# COMPANY_NAME=Your Company Name
# COMPANY_ADDRESS=123 Main St
# COMPANY_CITY=City, ZIP
# COMPANY_PHONE=+33 1 23 45 67 89
# COMPANY_EMAIL=contact@company.com
EOF
    echo ""
    echo "NOTE: Edit .env with your database credentials before running."
    echo ""
fi

# 6. Database schema
if [ -f "setup_tables.sql" ]; then
    echo ""
    echo "To initialize the database, run:"
    echo "  psql -U \$DB_USER -h \$DB_HOST -d \$DB_NAME -f setup_tables.sql"
    echo ""
fi

# 7. Run the application
echo ""
echo "Setup complete! To run the application:"
echo "  source venv/bin/activate"
echo "  python3 main.py"
echo ""
