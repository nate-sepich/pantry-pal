#!/bin/bash

# Quick code checks for CI/CD readiness
echo "🔍 Quick Code Quality Check"

# 1. Format check
echo "1️⃣ Checking formatting..."
python3 -m black --check --diff . > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Formatting: PASS"
    FORMAT_OK=1
else
    echo "❌ Formatting: FAIL"
    echo "   Fix with: python3 -m black ."
    FORMAT_OK=0
fi

# 2. Basic syntax check
echo "2️⃣ Checking Python syntax..."
python3 -m py_compile api/app.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Syntax: PASS"
    SYNTAX_OK=1
else
    echo "❌ Syntax: FAIL"
    SYNTAX_OK=0
fi

# Summary
echo ""
if [ $FORMAT_OK -eq 1 ] && [ $SYNTAX_OK -eq 1 ]; then
    echo "🎉 Ready for CI/CD!"
    exit 0
else
    echo "💥 Fix issues before pushing"
    exit 1
fi