#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Telegram Music Bot Deployment Script${NC}"
echo "================================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found! Please install Python 3.9+${NC}"
    exit 1
fi

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 not found! Please install pip${NC}"
    exit 1
fi

# Install system dependencies
echo -e "${YELLOW}📦 Installing system dependencies...${NC}"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt-get update
    sudo apt-get install -y ffmpeg python3-dev
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew install ffmpeg
fi

# Create virtual environment
echo -e "${YELLOW}🔧 Setting up virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo -e "${YELLOW}📥 Installing Python packages...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p data downloads logs

# Check .env file
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo -e "Please create .env file from .env.example"
    exit 1
fi

# Run bot
echo -e "${GREEN}✅ Setup complete! Starting bot...${NC}"
echo -e "${GREEN}🎵 Bot is running!${NC}"
python bot/main.py
