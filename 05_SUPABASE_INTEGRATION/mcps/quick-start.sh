#!/bin/bash

# MCP Integration Quick Start Script
# Sets up the environment and runs connection tests

set -e

echo "======================================================================"
echo "MCP INTEGRATION QUICK START"
echo "======================================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p logs
mkdir -p cache
echo "✅ Directories created"

# Check for .env file
echo ""
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo ""
    echo "Creating .env from example..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your API credentials!"
    echo ""
    read -p "Press Enter once you've added credentials to .env..."
else
    echo "✅ .env file found"
fi

# Check for required credentials
echo ""
echo "Checking credentials..."

missing_creds=0

if ! grep -q "WESTLAW_API_KEY=your_westlaw" .env; then
    echo "  ✅ Westlaw credentials configured"
else
    echo "  ⚠️  Westlaw credentials missing"
    missing_creds=1
fi

if ! grep -q "LEXISNEXIS_API_KEY=your_lexisnexis" .env; then
    echo "  ✅ LexisNexis credentials configured"
else
    echo "  ⚠️  LexisNexis credentials missing"
    missing_creds=1
fi

if [ -f "credentials.json" ]; then
    echo "  ✅ Gmail credentials.json found"
else
    echo "  ⚠️  Gmail credentials.json missing"
    missing_creds=1
fi

if ! grep -q "SLACK_OAUTH_TOKEN=xoxb-your" .env; then
    echo "  ✅ Slack credentials configured"
else
    echo "  ⚠️  Slack credentials missing"
    missing_creds=1
fi

if ! grep -q "SUPABASE_URL=https://your-project" .env; then
    echo "  ✅ Supabase credentials configured"
else
    echo "  ⚠️  Supabase credentials missing"
    missing_creds=1
fi

if ! grep -q "GITHUB_TOKEN=ghp_your" .env; then
    echo "  ✅ GitHub credentials configured"
else
    echo "  ⚠️  GitHub credentials missing"
    missing_creds=1
fi

# Run connection tests
echo ""
echo "======================================================================"
if [ $missing_creds -eq 1 ]; then
    echo "⚠️  Some credentials are missing."
    echo "Connection tests may fail for unconfigured services."
    echo ""
    read -p "Continue with tests anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Configure credentials and run again."
        exit 1
    fi
fi

echo ""
echo "Running connection tests..."
echo "======================================================================"
echo ""

python3 test-mcp-connections.py

echo ""
echo "======================================================================"
echo "SETUP COMPLETE"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. Review test results above"
echo "  2. Check mcp_test_results.json for details"
echo "  3. Run examples: python3 example-usage.py"
echo "  4. Review README.md for full documentation"
echo ""
echo "To activate environment in future sessions:"
echo "  source venv/bin/activate"
echo ""
