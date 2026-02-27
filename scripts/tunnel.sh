#!/bin/bash
# Start ngrok tunnel to expose Claude Code Manager to the internet
# Prerequisites: brew install ngrok && ngrok config add-authtoken YOUR_TOKEN

PORT=${1:-8000}

echo "Starting ngrok tunnel on port $PORT..."
echo "Once started, use the https URL shown below to access from your phone."
echo ""

ngrok http $PORT
