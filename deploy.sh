#!/bin/bash
set -e

# dev (default) → contract-extract-dev, target dev
# prod         → contract-extract-prod, target prod
ENV="${1:-dev}"
if [[ "$ENV" == "prod" ]]; then
  APP_NAME="contract-extract-prod"
  TARGET="prod"
else
  APP_NAME="contract-extract-dev"
  TARGET="dev"
fi

# Ajuste para o seu ambiente (variáveis de ambiente ou edite abaixo)
WORKSPACE_USER="${WORKSPACE_USER:-seu_usuario@empresa.com}"
PROFILE="${DATABRICKS_PROFILE:-seu_profile}"
WAREHOUSE_ID="${WAREHOUSE_ID:-YOUR_WAREHOUSE_ID}"
BUNDLE_NAME="contract-extract-app"
SOURCE_PATH="/Workspace/Users/${WORKSPACE_USER}/.bundle/${BUNDLE_NAME}/${TARGET}/files/app"

# Usar app config do target (dev/prod); se não existir, usar o exemplo
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
CONFIG_FILE="app/app.${TARGET}.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
  CONFIG_FILE="app/app.${TARGET}.example.yaml"
  echo "⚠️  Usando config de exemplo. Para produção: cp $CONFIG_FILE app/app.${TARGET}.yaml e preencha os valores."
fi
cp "$CONFIG_FILE" app/app.yaml

echo "🔨 Building frontend (ENV=${TARGET})..."
cd "$SCRIPT_DIR/app/frontend"
export REACT_APP_ENV="$TARGET"
npm run build

echo ""
echo "📦 Deploying bundle (target=${TARGET})..."
cd "$SCRIPT_DIR"
mkdir -p .databricks/bundle/${TARGET}/bin
databricks bundle deploy \
  --target "$TARGET" \
  --profile "$PROFILE" \
  --force-lock \
  --var catalog_name=seu_catalog \
  --var schema_name=contract_pdf \
  --var warehouse_id="$WAREHOUSE_ID"

echo ""
echo "🚀 Deploying app: ${APP_NAME}..."
databricks apps deploy "$APP_NAME" \
  --source-code-path "$SOURCE_PATH" \
  --profile "$PROFILE"

echo ""
echo "✅ Deploy completo!"
databricks apps get "$APP_NAME" --profile "$PROFILE" | grep -E "url|state"
