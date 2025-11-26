#!/bin/bash
# Build React frontend for Databricks Apps deployment
# This script must be run BEFORE 'databricks bundle deploy'

set -e

echo "🎨 Building React Frontend..."

# Check if app/frontend exists
if [ ! -d "app/frontend" ]; then
    echo "❌ Error: app/frontend directory not found"
    echo "   Make sure you're running this from the project root"
    exit 1
fi

cd app/frontend

# Install dependencies
echo "📦 Installing npm dependencies..."
npm install

# Build for production
echo "🔨 Building React app..."
npm run build

echo ""
echo "✅ Frontend build complete!"
echo "📦 app/frontend/build is ready for deployment"
echo ""
echo "Next step: databricks bundle deploy -t dev"
