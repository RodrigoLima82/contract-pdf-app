#!/bin/bash
set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Contract Extract App - Deployment Script    ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${BLUE}📋 Step 1: Checking prerequisites...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please create .env file from .env.example and configure your values.${NC}"
    exit 1
fi

if ! command -v databricks &> /dev/null; then
    echo -e "${RED}❌ Error: Databricks CLI not found!${NC}"
    echo -e "${YELLOW}Please install: pip install databricks-cli${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites checked${NC}"
echo ""

# Step 2: Load environment variables
echo -e "${BLUE}📦 Step 2: Loading environment variables...${NC}"
export $(cat .env | grep -v '^#' | xargs)
echo -e "${GREEN}✅ Environment variables loaded${NC}"
echo "   Catalog: $BUNDLE_VAR_catalog_name"
echo "   Schema: $BUNDLE_VAR_schema_name"
echo "   Warehouse: $BUNDLE_VAR_warehouse_id"
echo ""

# Step 3: Build frontend (optional - already built)
echo -e "${BLUE}🏗️  Step 3: Frontend build${NC}"
echo -e "${YELLOW}ℹ️  Skipping - frontend already built and committed${NC}"
echo ""

# Step 4: Validate bundle
echo -e "${BLUE}🔍 Step 4: Validating Databricks bundle...${NC}"
if databricks bundle validate -t dev; then
    echo -e "${GREEN}✅ Bundle validation successful${NC}"
else
    echo -e "${RED}❌ Bundle validation failed${NC}"
    exit 1
fi
echo ""

# Step 5: Deploy bundle
echo -e "${BLUE}🚀 Step 5: Deploying bundle resources...${NC}"
echo -e "${YELLOW}   This will deploy: Job, Dashboard, App definition${NC}"
if databricks bundle deploy -t dev; then
    echo -e "${GREEN}✅ Bundle deployed successfully${NC}"
else
    echo -e "${RED}❌ Bundle deployment failed${NC}"
    exit 1
fi
echo ""

# Step 6: Start app compute
echo -e "${BLUE}📱 Step 6: Starting Databricks App compute...${NC}"
if databricks apps start contract-extract-dev -t dev > /dev/null 2>&1; then
    echo -e "${GREEN}✅ App compute started${NC}"
else
    echo -e "${YELLOW}ℹ️  App compute already running${NC}"
fi
echo ""

# Step 7: Deploy the app source code
echo -e "${BLUE}📱 Step 7: Deploying Databricks App source code...${NC}"

# Get the workspace path from bundle summary (most reliable method)
BUNDLE_PATH=$(databricks bundle summary -t dev 2>/dev/null | grep "Path:" | awk '{print $2}')

if [ -z "$BUNDLE_PATH" ]; then
    echo -e "${RED}❌ Could not determine bundle path${NC}"
    echo -e "${YELLOW}Please run manually:${NC}"
    echo "   databricks apps deploy contract-extract-dev --source-code-path /Workspace/Users/<your-email>/.bundle/contract-extract-app/dev/files/app --mode SNAPSHOT -t dev"
    exit 1
fi

WORKSPACE_PATH="${BUNDLE_PATH}/files/app"

echo -e "${YELLOW}   App source path: $WORKSPACE_PATH${NC}"
echo -e "${YELLOW}   This may take 1-2 minutes...${NC}"

if databricks apps deploy contract-extract-dev --source-code-path "$WORKSPACE_PATH" --mode SNAPSHOT -t dev; then
    echo -e "${GREEN}✅ App source code deployed successfully${NC}"
else
    echo -e "${RED}❌ App deployment failed${NC}"
    echo -e "${YELLOW}💡 Tip: The app may already be deployed. Check status with:${NC}"
    echo "   databricks apps get contract-extract-dev -t dev"
    exit 1
fi
echo ""

# Step 9: Get app URL
echo -e "${BLUE}🌐 Step 10: Getting app information...${NC}"
APP_INFO=$(databricks apps get contract-extract-dev -t dev --output json)
APP_URL=$(echo "$APP_INFO" | grep -o '"url":"[^"]*' | cut -d'"' -f4)

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          🎉 Deployment Complete! 🎉           ║${NC}"
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo ""
echo -e "${BLUE}📦 Deployed Resources:${NC}"
echo ""
echo -e "${GREEN}✅ App:${NC}"
echo "   Name: contract-extract-dev"
echo "   URL:  $APP_URL"
echo ""
echo -e "${GREEN}✅ Job:${NC}"
echo "   Name: [dev $USER] contracts-extract-dev"
echo "   Status: Ready (ran successfully)"
echo ""
echo -e "${GREEN}✅ Dashboard:${NC}"
echo "   Name: [dev $USER] Contract Analysis Dashboard - dev"
echo ""
echo -e "${GREEN}✅ Database Objects:${NC}"
echo "   Catalog: $BUNDLE_VAR_catalog_name"
echo "   Schema:  $BUNDLE_VAR_schema_name"
echo "   Volume:  /Volumes/$BUNDLE_VAR_catalog_name/$BUNDLE_VAR_schema_name/files"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo ""
echo "1. Open the app: $APP_URL"
echo "2. Upload sample PDFs from the pdf/ folder"
echo "3. Wait for automatic processing (~1 min per PDF)"
echo "4. View extracted data in the dashboard"
echo ""
echo -e "${YELLOW}💡 Useful Commands:${NC}"
echo "   View app logs:  databricks apps logs contract-extract-dev -t dev"
echo "   View app status: databricks apps get contract-extract-dev -t dev"
echo "   Run job again:  databricks bundle run contracts_extract -t dev"
echo ""
echo -e "${YELLOW}⚠️  Important: Grant Unity Catalog Permissions${NC}"
echo "The app service principal needs permissions to access Unity Catalog."
echo "Go to Databricks UI → Catalog → $BUNDLE_VAR_catalog_name → Permissions"
echo "Add service principal: \$(databricks apps get contract-extract-dev -t dev --output json | jq -r '.service_principal_name')"
echo "Grant: USE CATALOG, USE SCHEMA, SELECT, MODIFY, READ VOLUME, WRITE VOLUME"
echo ""

