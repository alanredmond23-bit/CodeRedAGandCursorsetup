#!/bin/bash

# Antigravity Cloud Orchestration Setup Script
# Automates initial setup and verification

set -e

echo "=========================================="
echo "Antigravity Cloud Orchestration Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python 3.9+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python version: $PYTHON_VERSION${NC}"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install dependencies
echo ""
echo "Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p logs
mkdir -p checkpoints
mkdir -p outputs
mkdir -p templates
echo -e "${GREEN}✓ Directories created${NC}"

# Copy .env.example to .env if not exists
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env file with your actual credentials${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists${NC}"
fi

# Verify configuration files
echo ""
echo "Verifying configuration files..."
if [ -f "antigravity-config.yaml" ]; then
    echo -e "${GREEN}✓ antigravity-config.yaml found${NC}"
else
    echo -e "${RED}✗ antigravity-config.yaml missing${NC}"
fi

if [ -f "agent-mapping.yaml" ]; then
    echo -e "${GREEN}✓ agent-mapping.yaml found${NC}"
else
    echo -e "${RED}✗ agent-mapping.yaml missing${NC}"
fi

# Check GCP credentials
echo ""
echo "Checking GCP credentials..."
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo -e "${YELLOW}⚠ GOOGLE_APPLICATION_CREDENTIALS not set${NC}"
    echo "  Please set this environment variable to your service account key path"
else
    if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo -e "${GREEN}✓ GCP credentials file found${NC}"
    else
        echo -e "${RED}✗ GCP credentials file not found at: $GOOGLE_APPLICATION_CREDENTIALS${NC}"
    fi
fi

# Test imports
echo ""
echo "Testing Python imports..."
python3 -c "
import asyncio
import yaml
import httpx
import asyncpg
from google.cloud import aiplatform
from supabase import create_client
print('All imports successful')
" 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All Python dependencies working${NC}"
else
    echo -e "${RED}✗ Some imports failed${NC}"
fi

# Display next steps
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your credentials:"
echo "   ${YELLOW}nano .env${NC}"
echo ""
echo "2. Set up GCP authentication:"
echo "   ${YELLOW}export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json${NC}"
echo ""
echo "3. Verify configuration:"
echo "   ${YELLOW}python3 health-check.py${NC}"
echo ""
echo "4. Run the sync orchestrator:"
echo "   ${YELLOW}python3 crew-sync.py${NC}"
echo ""
echo "For detailed documentation, see README.md"
echo ""
