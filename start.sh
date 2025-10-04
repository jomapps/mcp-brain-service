#!/bin/bash

# Load environment variables from .env file
set -a
source .env
set +a

# Start the service (without reload for production stability)
./venv/bin/python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8002 --no-access-log

