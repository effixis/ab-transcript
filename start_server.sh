#!/bin/bash

# Start the Flask API server
echo "🚀 Starting Flask API Server..."
echo "Server will be available at http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask server using Poetry
poetry run python -m src.server.app