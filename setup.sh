#!/bin/bash

# Setup script for first-time installation

echo "🚀 Setting up Market Brief Backend..."
echo "===================================="

# 1. Create Python virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv

# 2. Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# 3. Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# 4. Install dependencies
echo "📚 Installing Python packages..."
pip install -r requirements.txt

# 5. Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   - FINLIGHT_API_KEY"
    echo "   - GEMINI_API_KEY"
fi

echo ""
echo "===================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Run: source venv/bin/activate"
echo "3. Start everything: ./run.sh"
echo "===================================="