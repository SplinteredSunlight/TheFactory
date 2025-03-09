#!/bin/bash
# setup-dev-env.sh - Script to set up the development environment for AI-Orchestration-Platform

set -e

# Print colored output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up development environment for AI-Orchestration-Platform...${NC}"

# Check prerequisites
echo -e "${GREEN}Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed. Please install Node.js first.${NC}"
    exit 1
fi

echo -e "${GREEN}All prerequisites are installed.${NC}"

# Create virtual environment
echo -e "${GREEN}Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Install Node.js dependencies
echo -e "${GREEN}Installing Node.js dependencies...${NC}"
cd src/frontend
npm install
cd ../..

# Set up environment variables
echo -e "${GREEN}Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    cp config/example.env .env
    echo -e "${YELLOW}Please update the .env file with your actual values.${NC}"
fi

# Create necessary directories
echo -e "${GREEN}Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p data

# Set up git hooks
echo -e "${GREEN}Setting up git hooks...${NC}"
if [ -d .git ]; then
    cp scripts/pre-commit.sh .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo -e "${GREEN}Git hooks installed.${NC}"
else
    echo -e "${YELLOW}Not a git repository. Skipping git hooks setup.${NC}"
fi

echo -e "${GREEN}Development environment setup complete!${NC}"
echo -e "${YELLOW}To start the development environment, run:${NC}"
echo -e "${YELLOW}docker-compose up -d${NC}"
