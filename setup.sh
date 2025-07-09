#!/bin/bash

echo "🧹 Removing old venv..."
rm -rf .venv

echo "🐍 Creating new virtual env with Python 3.10..."
uv venv --python=3.10

echo "⚙️ Activating env and installing dependencies..."
source .venv/Scripts/activate
uv pip install -r requirements.txt

echo "✅ Ready to go!"
