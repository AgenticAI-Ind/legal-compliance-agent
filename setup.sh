#!/bin/bash

# Legal & Compliance Agent Setup Script

set -e

echo "=========================================="
echo "Legal & Compliance Agent - Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check Python version
echo "Checking Python version..."
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [ "$(printf '%s\n' "3.11" "$PYTHON_VERSION" | sort -V | head -n1)" = "3.11" ]; then
        PYTHON_CMD=python3
    else
        print_error "Python 3.11+ required. Found: Python $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.11+"
    exit 1
fi

print_status "Python found: $($PYTHON_CMD --version)"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    print_status "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate || source venv/Scripts/activate 2>/dev/null || {
    print_error "Failed to activate virtual environment"
    exit 1
}
print_status "Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip -q
print_status "pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt -q
print_status "Dependencies installed"

# Download spaCy model
echo ""
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm
print_status "spaCy model downloaded"

# Create .env file if it doesn't exist
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    print_status ".env file created"
    print_warning "Please edit .env and add your configuration (especially OPENAI_API_KEY if using OpenAI)"
else
    print_warning ".env file already exists"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p data/uploads
mkdir -p logs
mkdir -p ~/.legal-compliance-agent/chroma
print_status "Directories created"

# Check if Docker is available
echo ""
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    print_status "Docker found: $(docker --version)"
    echo ""
    echo "You can start the full stack with:"
    echo "  docker-compose up -d"
else
    print_warning "Docker not found. You'll need to set up PostgreSQL and ChromaDB manually."
fi

# Print success message
echo ""
echo "=========================================="
echo -e "${GREEN}Setup completed successfully!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your environment:"
echo "   nano .env"
echo ""
echo "2. Start the API server:"
echo "   uvicorn src.main:app --reload"
echo ""
echo "   Or with Docker:"
echo "   docker-compose up -d"
echo ""
echo "3. Access the API:"
echo "   http://localhost:8000"
echo "   http://localhost:8000/docs (Swagger UI)"
echo ""
echo "4. Run tests:"
echo "   pytest"
echo ""
echo "5. Try the examples:"
echo "   python examples/example_usage.py"
echo ""
echo "For more information, see README.md"
echo ""

# Check if OpenAI key is set
if [ -f ".env" ]; then
    if grep -q "OPENAI_API_KEY=your-openai-api-key-here" .env || grep -q "OPENAI_API_KEY=$" .env; then
        print_warning "Remember to set your OPENAI_API_KEY in .env for enhanced features"
    fi
fi

echo "=========================================="
