#!/bin/bash
#
# Quick start script for code_generation.py
# Handles all dependencies automatically
#

set -e  # Exit on error

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON="${PYTHON:-python3}"

echo "=========================================="
echo "  Code Generation Tool - Quick Start"
echo "=========================================="
echo

# Check if Python 3.11+ is available
if ! command -v $PYTHON &> /dev/null; then
    echo "Error: Python 3 not found. Please install Python 3.11 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python $REQUIRED_VERSION or higher required (found $PYTHON_VERSION)"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Warning: Docker is not running or not installed."
    echo "Docker is required for code execution."
    echo
    read -p "Continue anyway? (y/n) [n]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Check if dependencies are installed
if [ ! -f "$VENV_DIR/.dependencies_installed" ]; then
    echo "Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -e "$PROJECT_DIR"
    touch "$VENV_DIR/.dependencies_installed"
    echo "✓ Dependencies installed"
    echo
else
    echo "✓ Dependencies already installed"
    echo
fi

# Check for .env file
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "Warning: No .env file found"
    echo
    echo "Please create a .env file with your API key:"
    echo "  ANTHROPIC_API_KEY=your-api-key-here"
    echo

    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "You can also set the environment variable directly:"
        echo "  export ANTHROPIC_API_KEY='your-api-key-here'"
        echo
    fi
fi

# Run the code generation tool
echo "Starting code generation tool..."
echo
$PYTHON "$PROJECT_DIR/code_generation.py" "$@"
