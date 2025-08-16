#!/bin/bash

# Local linting script for PantryPal
# Run this before pushing to avoid CI/CD failures

echo "🔍 Running local code quality checks..."

# Change to project directory
cd "$(dirname "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if any checks fail
FAILED=0

echo -e "\n1️⃣ ${YELLOW}Code Formatting Check (Black)${NC}"
python3 -m black --check --diff .
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Formatting issues found!${NC}"
    echo -e "${YELLOW}💡 Fix with: python3 -m black .${NC}"
    FAILED=1
else
    echo -e "${GREEN}✅ Code formatting is good!${NC}"
fi

echo -e "\n2️⃣ ${YELLOW}Linting Check (Ruff)${NC}"
python3 -m ruff check .
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Linting issues found!${NC}"
    echo -e "${YELLOW}💡 Fix with: python3 -m ruff check . --fix${NC}"
    FAILED=1
else
    echo -e "${GREEN}✅ Linting passed!${NC}"
fi

echo -e "\n3️⃣ ${YELLOW}Security Check (Bandit)${NC}"
python3 -m bandit -r api/ -x api/tests/ -ll
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Security issues found!${NC}"
    FAILED=1
else
    echo -e "${GREEN}✅ Security check passed!${NC}"
fi

echo -e "\n4️⃣ ${YELLOW}Dependency Vulnerability Check (Safety)${NC}"
cd api && python3 -m safety check
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Vulnerable dependencies found!${NC}"
    FAILED=1
else
    echo -e "${GREEN}✅ Dependencies are secure!${NC}"
fi

# Summary
echo -e "\n📊 ${YELLOW}Summary${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed! Safe to push to GitHub.${NC}"
    exit 0
else
    echo -e "${RED}💥 Some checks failed. Fix issues before pushing.${NC}"
    exit 1
fi