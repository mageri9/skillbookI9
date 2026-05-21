echo "=================================="
echo " GitHub Profiler Pre-Commit Check "
echo "=================================="

echo
echo "[1/5] Ruff lint..."
ruff check .

if [ $? -ne 0 ]; then
    echo
    echo "❌ Ruff lint failed"
    exit 1
fi

echo
echo "[2/5] Ruff format..."
ruff format --check .

if [ $? -ne 0 ]; then
    echo
    echo "❌ Formatting issues found"
    echo "Run: ruff format ."
    exit 1
fi

echo
echo "[3/5] MyPy..."
mypy github_profiler

if [ $? -ne 0 ]; then
    echo
    echo "❌ MyPy failed"
    exit 1
fi

echo
echo "[4/5] Pytest..."
pytest

if [ $? -ne 0 ]; then
    echo
    echo "❌ Tests failed"
    exit 1
fi

echo
echo "[5/5] Git status..."
git status --short

echo
echo "✅ Pre-commit checks passed"

echo "🔧 Auto-fixing..."

ruff check . --fix
ruff format .

echo
echo "✅ Done"

# bash scripts/check.sh