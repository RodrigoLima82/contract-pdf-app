# 📄 Contract Extract App

AI-powered contract information extraction using Databricks Apps, GPT-5, and Unity Catalog.

> **📌 Note:** Sample PDFs contain fictional data for demonstration purposes only.

## 🎯 What It Does

- **Upload** contract PDFs to Unity Catalog Volume
- **Auto-extract** 19+ structured fields using AI (parties, values, dates, terms, etc.)
- **Chat** with your contracts using natural language (Genie)
- **Dashboard** with analytics and visualizations

**Stack:** React + FastAPI + Unity Catalog + Agent Bricks + Serverless Compute

---

## 🚀 Quick Deploy to Databricks

### Prerequisites

- Databricks Workspace (Premium/Enterprise)
- Unity Catalog enabled
- SQL Warehouse (Serverless recommended)
- Databricks CLI installed: `pip install databricks-cli`
- **Agent Bricks (Multi-Agent System) and Genie Agent** configured

#### AI Agents Setup (Required)

This project uses **Agent Bricks** as a multi-agent orchestration system that calls the **Genie agent** for natural language queries over your data.

**Before deploying, you need to:**

1. **Create a Genie Agent:**
   - Create a new Genie space configured with your Unity Catalog and add Contract Extract Table

2. **Configure Agent Bricks Multi-Agent:**
   - Set up an Agent Bricks multi-agent system
   - Configure it to call your Genie agent
   - Note the agent endpoint name

3. **Update `.env` file:**
   - Set `BUNDLE_VAR_agent_endpoint` to your Agent Bricks endpoint name
   - Set `BUNDLE_VAR_audio_endpoint` to your Whisper audio transcription endpoint (if using voice)

> **Note:** The chat functionality requires these agents to be properly configured. Without them, natural language queries will not work.

### 1. Clone Repository

```bash
git clone https://github.com/Databricks-BR/contract-extract-app.git
cd contract-extract-app
```

### 2. Configure Environment Variables

Copy the example file and configure your values:

```bash
cp .env.example .env
```

Then edit `.env` with your Databricks credentials:

```bash
# Databricks Authentication
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your_databricks_personal_access_token

# Bundle Variables (using BUNDLE_VAR_ prefix for Databricks Asset Bundles)
BUNDLE_VAR_catalog_name=your_catalog_name
BUNDLE_VAR_schema_name=your_schema_name
BUNDLE_VAR_volume_name=your_volume_name
BUNDLE_VAR_warehouse_id=your_warehouse_id
BUNDLE_VAR_agent_endpoint=your_agent_endpoint_name
BUNDLE_VAR_audio_endpoint=your_audio_endpoint_name
BUNDLE_VAR_llm_endpoint=your_llm_endpoint_name
```

**Get Warehouse ID:** Databricks UI → SQL Warehouses → Select warehouse → URL contains ID  
**Get Token:** Databricks UI → User Settings → Access Tokens → Generate new token


### 3. Create Unity Catalog Resources (Manual Setup Required)

Before deploying, you need to manually create the Unity Catalog resources:

1. **Create Catalog** (if it doesn't exist):
   ```sql
   CREATE CATALOG IF NOT EXISTS your_catalog_name;
   USE CATALOG your_catalog_name;
   ```

2. **Create Schema**:
   ```sql
   CREATE SCHEMA IF NOT EXISTS your_schema_name;
   USE SCHEMA your_schema_name;
   ```

3. **Create Volume** for PDF files:
   ```sql
   CREATE VOLUME IF NOT EXISTS your_schema_name.files;
   ```

You can run these commands in:
- Databricks SQL Editor
- Databricks Notebook
- Or via CLI: `databricks sql execute -s "<sql_query>"`

### 4. Build Frontend

> **Note:** Built frontend is already included in the repository. Skip this step for quick deployment.

If you modified the frontend code:
```bash
./build_frontend.sh
```

Or manually:
```bash
cd app/frontend
npm install
npm run build
```

### 5. Deploy with DABS

**Option A: Automated Deployment (Recommended)**

Use the deployment script that automates all steps:

```bash
./deploy.sh
```

The script will:
- ✅ Validate your configuration
- ✅ Deploy all bundle resources (Job, Dashboard, App)
- ✅ Run the setup job to create tables
- ✅ Deploy the Databricks App
- ✅ Display your app URL and next steps

**Option B: Manual Deployment**

If you prefer to run steps manually:

```bash
# Load environment variables and validate
databricks bundle validate -t dev

# Deploy bundle
databricks bundle deploy -t dev

# Run setup job
databricks bundle run contracts_extract -t dev

# Deploy app
USER_EMAIL=$(databricks current-user me --output json | grep -o '"userName":"[^"]*' | cut -d'"' -f4)
databricks apps deploy contract-extract-dev \
  --source-code-path "/Workspace/Users/${USER_EMAIL}/.bundle/contract-extract-app/dev/files/app" \
  --mode SNAPSHOT -t dev
```

**What gets deployed:**
- ✅ Databricks App (frontend + backend)
- ✅ Job with 4 tasks (setup → track → list → extract)
- ✅ Lakeview Dashboard (analytics and visualizations)
- ✅ Unity Catalog Schema and Volume
- ✅ Database Tables (contract_track, contract_parsed, contract_extract)

**After deployment, you'll receive:**
- 🌐 App URL to access the application
- 📊 Dashboard embedded in the app
- 💡 Next steps and useful commands

### 6. Configure Unity Catalog Permissions (Required)

The app needs permissions to access Unity Catalog resources. Choose one of the following authentication methods:

#### Option A: Service Principal Authentication

Grant permissions directly to the app's service principal. This is the most secure and recommended approach.

1. **Grant permissions via Databricks UI:**
   - Go to **Databricks UI** → **Catalog** → Your catalog name
   - Click **Permissions** tab
   - Click **Grant** button
   - Search for the service principal name from step 1
   - Grant the following privileges:
     - ✅ `USE CATALOG`
     - ✅ `USE SCHEMA` on your schema
     - ✅ `SELECT` on your schema
     - ✅ `MODIFY` on your schema

> **Note:** Volume permissions (`READ_VOLUME`, `WRITE_VOLUME`) are automatically configured during app deployment.

#### Option B: User Authorization (On-Behalf-Of)

Allow users to access the app using their own credentials. The app will execute queries on behalf of the logged-in user.

**Steps:**

1. **Enable On-Behalf-Of User Authorization:**

2. **Grant permissions to users:**
    - ✅ `USE CATALOG`
    - ✅ `USE SCHEMA` on your schema
    - ✅ `SELECT` on your schema
    - ✅ `MODIFY` on your schema
    - ✅ `READ VOLUME` on your volume
    - ✅ `WRITE VOLUME` on your volume

---

## 📁 Project Structure

```
contract-extract-app/
├── app/
│   ├── backend/              # FastAPI
│   ├── frontend/             # React
│   │   └── build/           # Built frontend (committed for easy deploy)
│   ├── app.yaml             # App config
│   └── requirements.txt
├── jobs/                    # Databricks notebooks
│   ├── 1_incremental_pdf_track.py
│   ├── 2_list_files.py
│   └── 3_pdf_parse_extract.sql
├── resources/
│   ├── app.yml              # DABS app definition
│   ├── jobs.yml             # DABS job definition
│   └── dashboard.yml        # DABS dashboard definition
├── databricks.yml           # Main DABS config
├── build_frontend.sh        # Build script
├── deploy.sh                # Automated deployment script
├── .env.example             # Environment variables template
└── README.md
```

---

## 🎨 Usage

### Upload Contracts for Testing

The repository includes sample PDFs in the `pdf/` folder for testing:
- `contrato-001-techsolutions.pdf`
- `contrato-002-auditec.pdf`

**To upload PDFs:**

1. Open the deployed app in your browser (get URL from `databricks apps get contract-extract-dev -t dev`)
2. Click **"Upload PDF"** button
3. Select contract PDF files (use the samples from `pdf/` folder or your own)
4. Files are stored in Unity Catalog Volume: `/Volumes/{catalog}/{schema}/{volume}/`

### Automatic Processing

**File Arrival Trigger** automatically processes new PDFs:
- 📄 PDF uploaded → Job triggers within ~1 minute
- 🤖 AI extracts data → Results in `contract_extract` table
- ✅ View in app → Data appears automatically

### Extracted Fields (19 total)

- Contract type, name, parties (contractor/contracted)
- Financial: amount, currency, payment terms
- Dates: signature, start, end, duration
- Legal: termination clause, penalties, guarantees, confidentiality, jurisdiction
- Summary and observations

### Query via API

```bash
# All contracts
curl http://your-app-url/api/all_data

# Specific contract
curl http://your-app-url/api/pdf_info?pdf=contract-001.pdf

# Chat (if Genie configured)
curl -X POST http://your-app-url/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show contracts expiring this year"}'
```

---

## 🛠️ Troubleshooting

### "Table not found"
Run the setup job to create tables (see Step 5 above).

### "No data in table"
1. Upload PDFs to the volume
2. Wait ~1 minute for auto-trigger, or manually run the job
3. Check job run status in Databricks UI → Workflows

### Frontend shows empty
- Check SQL Warehouse is running
- Verify `warehouse_id` in `databricks.yml`
- Check app logs: `databricks apps logs your-app-name`

### Authentication errors
- Verify Databricks CLI is configured: `databricks auth profiles`
- For Genie chat: ensure secret scope/key contain valid PAT

---

## 📊 Data Model

**contract_track** - File tracking
- Columns: `file_name`, `file_path`, `type`, `size`, `processed`, `upload_time`, `processed_time`, `file_hash`

**contract_parsed** - Raw parsed content
- Columns: `path`, `raw_parsed`, `text`, `summarize`, `error_status`

**contract_extract** - Structured data (19 fields)
- See "Extracted Fields" section above

---

## 🔐 Security

- ✅ `.env` file is automatically git-ignored - never commit credentials
- Use Databricks Secrets for PATs and tokens
- All data stored in Unity Catalog with RBAC
- Change Data Feed enabled for audit trails
- Environment variables keep sensitive data out of config files

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push: `git push origin feature/name`
5. Open Pull Request

---

## 📚 Resources

- [Databricks Apps](https://docs.databricks.com/applications/apps/)
- [Databricks Asset Bundles (DABS)](https://docs.databricks.com/dev-tools/bundles/)
- [Unity Catalog](https://docs.databricks.com/unity-catalog/)
- [AI Functions](https://docs.databricks.com/sql/language-manual/functions/ai_query.html)
