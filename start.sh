#!/bin/bash

# Evo-AI Quick Start Script

set -e

echo "====================================="
echo "  EVO-AI PLATFORM QUICK START"
echo "====================================="
echo

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo "   Creating from .env.example..."
    cp .env.example .env
    echo
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY=sk-ant-..."
    echo "   - OPENAI_API_KEY=sk-..."
    echo
    read -p "Press Enter after adding your API keys to .env..."
fi

echo "1. Starting Docker services..."
docker-compose up -d

echo
echo "2. Waiting for services to be ready..."
sleep 10

echo
echo "3. Running database migrations..."
docker-compose exec -T backend alembic upgrade head

echo
echo "====================================="
echo "  ✅ EVO-AI IS RUNNING!"
echo "====================================="
echo
echo "Access the platform:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8002"
echo "  API Docs:  http://localhost:8002/docs"
echo
echo "View logs:"
echo "  docker-compose logs -f"
echo
echo "Stop services:"
echo "  docker-compose down"
echo
echo "Run evolution demo:"
echo "  python examples/sorting_evolution.py"
echo
echo "====================================="
