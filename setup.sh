#This SetUP is for:Github bash / WINDOWS SYSTEM)  / UV  venv
# ./setup.sh
echo "🧹 Removing old venv..."
rm -rf .venv
rm -rf .python-version
rm -rf pyproject.toml
rm -rf uv.lock

echo "🐍 Creating new virtual env with Python 3.10..."
uv venv --python=3.10 .venv --verbose
pip install uv
uv init

echo "⚙️ Activating env and installing dependencies..."
source .venv/Scripts/activate # For Mac  .venv/bin/activate
uv pip install -r requirements.txt
python -m spacy download en_core_web_sm

echo "✅ Ready to go!"
