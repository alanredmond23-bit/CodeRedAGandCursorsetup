#!/bin/bash

# Discovery Pipeline Quick Start Script
# Sets up the pipeline for first-time use

set -e

echo "🚀 Discovery Pipeline Quick Start"
echo "=================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 20.x or higher."
    exit 1
fi

echo "✓ Node.js $(node --version) detected"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm."
    exit 1
fi

echo "✓ npm $(npm --version) detected"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install

# Create directory structure
echo ""
echo "📁 Creating directory structure..."
mkdir -p discovery-docs
mkdir -p case-files
mkdir -p config
mkdir -p tests
mkdir -p output
mkdir -p dashboard

# Create .gitkeep files
touch discovery-docs/.gitkeep
touch case-files/.gitkeep

echo "✓ Directory structure created"

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys and credentials"
fi

# Check for required tools
echo ""
echo "🔧 Checking for optional tools..."

if command -v gh &> /dev/null; then
    echo "✓ GitHub CLI detected"
else
    echo "⚠️  GitHub CLI not found. Install with: brew install gh"
fi

if command -v vercel &> /dev/null; then
    echo "✓ Vercel CLI detected"
else
    echo "⚠️  Vercel CLI not found. Install with: npm i -g vercel"
fi

# Display next steps
echo ""
echo "✅ Quick start complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Edit .env and add your API keys"
echo "  2. Configure GitHub Secrets (see SETUP.md)"
echo "  3. Set up Supabase database (see SETUP.md)"
echo "  4. Add discovery documents to discovery-docs/"
echo "  5. Commit and push to trigger the pipeline"
echo ""
echo "📖 For detailed setup instructions, see SETUP.md"
echo "📖 For usage documentation, see README.md"
echo ""
echo "🎉 Happy processing!"
