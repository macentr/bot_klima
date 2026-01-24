#!/bin/bash
# Pre-push checklist - Run this before pushing to GitHub
# Usage: bash scripts/prepush.sh

set -e

echo "🔍 Running pre-push checks..."
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# 1. Check for uncommitted changes
echo "1️⃣  Checking for uncommitted changes..."
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: There are uncommitted changes"
    git status
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo "   ✅ OK"
echo ""

# 2. Check for .env in staging
echo "2️⃣  Checking for .env files..."
if git diff --cached --name-only | grep -E '^\.env|env\.'; then
    echo "❌ Error: .env files detected in staging area"
    echo "   Please use 'git reset HEAD .env' to unstage"
    exit 1
fi
echo "   ✅ OK"
echo ""

# 3. Lint with ruff
echo "3️⃣  Running ruff lint..."
if ! ruff check app/; then
    echo "❌ Linting failed"
    echo "   Fix issues with: ruff check app/ --fix"
    exit 1
fi
echo "   ✅ OK"
echo ""

# 4. Format check with ruff
echo "4️⃣  Checking code format..."
if ! ruff format --check app/; then
    echo "❌ Formatting issues found"
    echo "   Fix with: ruff format app/"
    exit 1
fi
echo "   ✅ OK"
echo ""

# 5. Type checking
echo "5️⃣  Running type checks (pyright)..."
if command -v pyright &> /dev/null; then
    if ! pyright app/; then
        echo "⚠️  Type check warnings (non-blocking)"
    fi
    echo "   ✅ OK"
else
    echo "⚠️  pyright not installed, skipping"
fi
echo ""

# 6. Run tests
echo "6️⃣  Running tests..."
if command -v pytest &> /dev/null; then
    if ! pytest tests/ -q; then
        echo "❌ Tests failed"
        exit 1
    fi
    echo "   ✅ OK"
else
    echo "⚠️  pytest not installed, skipping"
fi
echo ""

# 7. Check git log for proper messages
echo "7️⃣  Checking commit messages..."
commits_to_push=$(git rev-list origin/$(git rev-parse --abbrev-ref HEAD)..HEAD 2>/dev/null || echo "")
if [ -n "$commits_to_push" ]; then
    echo "   Commits to push:"
    git log --oneline origin/$(git rev-parse --abbrev-ref HEAD)..HEAD
    echo "   ✅ Verify these commits look good"
else
    echo "   ✅ No new commits"
fi
echo ""

# 8. Check branch protection
echo "8️⃣  Checking branch..."
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" = "main" ]; then
    echo "❌ Error: You are on 'main' branch"
    echo "   Push to 'develop' or feature branch instead"
    exit 1
fi
echo "   ✅ Branch: $current_branch (OK)"
echo ""

echo "✅ All pre-push checks passed!"
echo ""
echo "Next steps:"
echo "  git push origin $current_branch"
echo "  Then open a Pull Request on GitHub"
echo ""
