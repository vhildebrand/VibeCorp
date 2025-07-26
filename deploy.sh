#!/bin/bash

# VibeCorp Deployment Script
# This script helps prepare the application for deployment

echo "🚀 VibeCorp Deployment Preparation"
echo "=================================="

# Check if required files exist
echo "📋 Checking deployment files..."

files=("Dockerfile" "railway.json" "requirements.txt" "DEPLOYMENT_GUIDE.md")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

# Check frontend files
frontend_files=("startup-simulator-ui/vercel.json" "startup-simulator-ui/package.json")
for file in "${frontend_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

echo ""
echo "🔧 Deployment Preparation Complete!"
echo ""
echo "Next Steps:"
echo "1. 🗄️  Set up your database (see DEPLOYMENT_GUIDE.md)"
echo "2. 🖥️  Deploy backend to Railway"
echo "3. 🌐 Deploy frontend to Vercel"
echo "4. 🔧 Configure environment variables"
echo ""
echo "📖 Full instructions: DEPLOYMENT_GUIDE.md"
echo ""

# Check if .env exists and has required variables
if [ -f ".env" ]; then
    echo "⚠️  Local .env file found - make sure to set production variables separately!"
    echo "   Required variables: OPENAI_API_KEY, DATABASE_URL"
    echo ""
fi

echo "🎉 Ready for deployment!"
echo "💡 Estimated monthly cost: $10-25 for moderate usage" 