#!/bin/bash

# Change to script directory
cd "$(dirname "$0")"

# Set SSL certificate path using uv run to ensure certifi is available
export SSL_CERT_FILE=$(uv run python -c "import certifi; print(certifi.where())")

# Run the bot
uv run python -m tts_bot
