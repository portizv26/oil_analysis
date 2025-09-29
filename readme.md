
# AI Comments Evaluator

A lightweight web app to **evaluate AI-generated comments** about mining equipm### AI Comments
- For the selected **AlertId**,## ☁️ Daily S3 Sync of `eval.db` & Analytics

We provide **two approaches** for data analysis:

### **1. In-App Analytics (Real-time)**
- Built-in **Analytics dashboard** for immediate insights
- Interactive visualizations and filtering
- Grade distribution analysis by comment type
- Notes analysis and evaluation patterns

### **2. External BI Analytics (Daily Export)**
Upload the SQLite to S3 every 24h for your backend BI systems.st **all** `CommentText` (grouped by `CommentType`).
- Evaluator opens each comment → reads the same context → **assigns one grade (1–7)** and optional note.
- Submit writes a row into `state/eval.db:evaluations`.
- "Next Alert" button iterates through pending Alerts.

---

## 📊 Analytics Dashboard

The **Analytics** page (`2_Analytics.py`) provides comprehensive insights into evaluation patterns and AI comment performance:

### **Grade Distribution Analysis**
- **Interactive boxplots** showing grade distribution by `CommentType`
- Visual comparison of AI model performance across different comment types
- Statistical summaries (mean, median, std dev, min/max) per comment type

### **Notes Analysis**
- **Notes by CommentType table** showing evaluator feedback patterns
- Comparison of average grades for evaluations with vs. without notes
- Detailed notes browser with filtering capabilities

### **Summary Metrics & Filtering**
- Dashboard overview: total evaluations, unique comments/alerts, average grades
- **Advanced filtering** by comment type, grade range, and notes presence
- Real-time data insights for evaluation quality monitoring

> **Use Case:** Track which AI models (`CommentType`) perform better, identify patterns in evaluator feedback, and monitor evaluation quality over time.onditions.  
Reads **static oil & telemetry data from Parquet**; stores evaluator feedback in a small **SQLite** file.

---

## 🧱 Architecture at a Glance

- **UI / App:** Streamlit (pure Python)
- **Base data (read-only Parquet):**
  - `data/oil_measurements.parquet`
  - `data/telemetry_measurements.parquet`
  - `data/alerts.parquet`
  - `data/ai_comments.parquet`
- **Mutable data (writes):** **SQLite** (`state/eval.db`)
  - `evaluations` (single grade 1–7 per AI comment, optional free-text note)

> One **Alert** may have **oil**, **telemetry**, or **both** sub-alerts. Evaluators see **all AI comments** for the chosen Alert and **grade each comment separately** (same context/figures for all comments under an Alert).

---

## 📂 Project Structure

ai-comments-evaluator/
├─ app/
│  ├─ streamlit_app.py
│  ├─ pages/
│  │  ├─ 1_Review.py          # main grading flow (context + comments + form)
│  │  ├─ 2_Analytics.py       # analytics dashboard with grade distributions & insights
│  ├─ utils/
│  │  ├─ db.py                # SQLite init/session
│  │  ├─ schemas.py           # SQLModel classes (evaluations)
│  │  ├─ io.py                # Parquet readers (oil/telemetry/alerts/comments)
├─ data/
│  ├─ oil_measurements.parquet
│  ├─ telemetry_measurements.parquet
│  ├─ alerts.parquet
│  ├─ ai_comments.parquet
├─ state/
│  └─ eval.db                 # created on first submission
└─ README.md

> **No heavy setup:** place Parquet files under `data/`; the app creates `state/eval.db` on first write.

---

## 🗄️ Data Contracts

### Parquet (read-only)

**`alerts.parquet`**
- `AlertId` (PK)
- `OilAlertId` (nullable), `TelAlertId` (nullable)
- `TimeStart`, `UnitId`, `Component`
- `Label` (optional: `oil_only` | `telemetry_only` | `both`)

**`oil_measurements.parquet`**
- `OilAlertId`, `SampleDate`, `UnitId`, `Component`
- `OilMeter` (optional)
- `ElementName`
- `Value`, `LimitValue` (optional)
- `IsLimitReached` (bool), `BreachLevel` (optional: `none` | `alert` | `critical` | `urgent`)

**`telemetry_measurements.parquet`**
- `TelAlertId`, `Timestamp`, `UnitId`, `Component`
- `ComponentMeter` (optional)
- `VariableName`
- `Value`, `UpperLimitValue` (optional), `LowerLimitValue` (optional)
- `IsLimitReached` (bool)

**`ai_comments.parquet`**
- `AICommentId`, `AlertId`
- `CommentText`
- `CommentType` (e.g., `baseline`, `prompt_v2`, `rule_based`, etc.)

### SQLite (writes)

**`evaluations`**
- `EvaluationId` (PK AUTOINCREMENT)
- `AICommentId` **(required)**, `AlertId` **(required)**
- `UserId` (optional)
- `Grade` **INT 1–7** *(single overall score per comment)*
- `Notes` **TEXT** (optional)
- `CreatedAt` **TIMESTAMP** (defaults to now)

> One **row = one evaluator’s grade for one AI comment** tied to a specific `AlertId`.

---

## 📊 What the UI Shows (Charts & Tables)

### Context (same for all comments under the Alert)

**Oil (if `OilAlertId` exists):**
1. **Snapshot table (latest per element)**  
   Columns: `ElementName | Value | LimitValue | BreachLevel | SampleDate`  
   Sorted with breached elements on top; visual badges for `BreachLevel`.

**Telemetry (if `TelAlertId` exists):**
1. **Top breaches table**  
   `VariableName | MaxExcess | AnyLimitReached | LastTimestamp`
2. **Variable trend chart (focused)**  
   Line chart over a recent window (e.g., ±48h) with upper/lower limit bands; optional rolling mean.

*(Charts use Plotly; no custom color theme required.)*

### AI Comments
- For the selected **AlertId**, list **all** `CommentText` (grouped by `CommentType`).
- Evaluator opens each comment → reads the same context → **assigns one grade (1–7)** and optional note.
- Submit writes a row into `state/eval.db:evaluations`.
- “Next Alert” button iterates through pending Alerts.

---

## 📝 Grading (1–7)

Single overall score per AI comment (same rubric applies to all):

- **1–2:** Very poor / irrelevant / unsafe.
- **3–4:** Partial understanding, mixed accuracy, vague actions.
- **5–6:** Good/very good, accurate and actionable.
- **7:** Excellent—concise, accurate, directly actionable; cites evidence from context.

Optional **Notes**: brief rationale or issues spotted.

---

## ☁️ Daily S3 Sync of `eval.db` (no in-app analytics)

We won’t build analytics in the app. Instead, we **upload the SQLite** to S3 every 24h for your backend BI.

**Python helper (uses env vars):**
```python
import os, boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

ACCESS_KEY = os.getenv('ACCESS_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
BUCKET_NAME = os.getenv('BUCKET_NAME')

def upload_to_s3(file_path, bucket_name=BUCKET_NAME, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_path)
    s3 = boto3.client('s3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )
    try:
        s3.upload_file(file_path, bucket_name, object_name)
        print(f"Uploaded '{file_path}' → s3://{bucket_name}/{object_name}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except NoCredentialsError:
        print("Credentials not available.")
    except PartialCredentialsError:
        print("Incomplete credentials provided.")
````

**Cron example (Linux/macOS):**

```
# Edit with: crontab -e
# Daily at 02:00 upload state/eval.db to S3 (adjust paths as needed)
0 2 * * * /usr/bin/python3 /path/to/scripts/upload_eval_db.py
```

Where `scripts/upload_eval_db.py` simply calls:

```python
from pathlib import Path
from upload_to_s3 import upload_to_s3

eval_db = Path(__file__).resolve().parents[1] / "state" / "eval.db"
upload_to_s3(str(eval_db), object_name="eval.db")
```

*(On Windows, use Task Scheduler with the same script.)*

---

## ⚙️ Running It

* Put Parquet files under `data/` following the contracts above.
* Launch: `streamlit run app/streamlit_app.py`
* Navigate between **Review** (evaluation) and **Analytics** (insights) pages via sidebar
* First submission creates `state/eval.db` automatically.

**SQLite indices recommended:**

* `CREATE INDEX IF NOT EXISTS idx_eval_comment ON evaluations(AICommentId);`
* `CREATE INDEX IF NOT EXISTS idx_eval_alert ON evaluations(AlertId);`
* `CREATE INDEX IF NOT EXISTS idx_eval_created ON evaluations(CreatedAt);`

**Performance tips:**

* Cache Parquet slices per `AlertId` (`st.cache_data`) for instant navigation.
* Keep `ai_comments.parquet` minimal (text + ids).

---

## 🛣️ Roadmap

1. Load a pilot set of Alerts with both oil/telemetry examples. -> Done
2. Build comprehensive analytics dashboard for real-time insights. -> Done
3. Collect evaluator grades daily; optionally offload `eval.db` to S3. 
4. Use built-in analytics + external BI for evaluation quality monitoring.
5. Iterate prompts/comment generators; add more `CommentType`s based on performance insights.

---
