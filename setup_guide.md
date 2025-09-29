# 🚀 Quick Start Guide - AI Comments Evaluator

## Recent Updates
- ✅ **Smart Alert Filtering**: Only shows alerts that have AI comments (no empty alerts)
- ✅ **Improved Layout**: Two-column design - Context data (left) and Comments (right)
- ✅ **Better Overview**: Dashboard shows alerts with/without comments

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Verify Data Files
Ensure your `data/` folder contains all required Parquet files:
- ✅ `alerts.parquet`
- ✅ `oil_measurements.parquet`  
- ✅ `telemetry_measurements.parquet`
- ✅ `ai_comments.parquet`

### 3. Run the Application
```bash
streamlit run app/streamlit_app.py
```

The app will be available at: http://localhost:8501

## Usage Workflow

### 📝 Evaluation Process
1. **Navigate to Review Page** - Click "Start Evaluating" or use sidebar
2. **Select Alert** - Choose from dropdown of available alerts
3. **Review Context** - Examine oil and telemetry data charts/tables
4. **Grade Comments** - Evaluate each AI comment on 1-7 scale
5. **Submit & Continue** - Save evaluations and move to next alert

### 🎯 Grading Scale
- **7 - Excellent:** Concise, accurate, directly actionable; cites evidence
- **5-6 - Good:** Accurate and actionable recommendations  
- **3-4 - Partial:** Mixed accuracy, vague actions
- **1-2 - Poor:** Irrelevant or potentially unsafe

## File Structure Created
```
oil_analysis/
├─ app/
│  ├─ streamlit_app.py           # Main app entry point
│  ├─ pages/
│  │  └─ 1_Review.py            # Evaluation workflow
│  └─ utils/
│     ├─ __init__.py            # Package init
│     ├─ schemas.py             # Data models & validation
│     ├─ db.py                  # SQLite operations
│     ├─ io.py                  # Parquet data loading
│     ├─ charts.py              # Plotly visualizations
│     └─ s3_sync.py             # AWS S3 backup
├─ data/                        # Your Parquet files (existing)
├─ state/                       # SQLite database (auto-created)
├─ scripts/
│  └─ upload_eval_db.py         # Daily S3 sync script
├─ requirements.txt             # Python dependencies
└─ SETUP_GUIDE.md              # This file
```

## S3 Backup Configuration (Optional)

### Environment Variables
```bash
# Windows
set AWS_ACCESS_KEY_ID=your_access_key
set AWS_SECRET_ACCESS_KEY=your_secret_key  
set AWS_S3_BUCKET=your_bucket_name

# Linux/Mac
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_S3_BUCKET=your_bucket_name
```

### Test S3 Connection
```bash
cd app/utils
python s3_sync.py test
```

### Manual Database Upload
```bash
cd scripts
python upload_eval_db.py
```

### Automated Daily Sync

**Windows Task Scheduler:**
- Task: Run `python C:\path\to\scripts\upload_eval_db.py`
- Schedule: Daily at 2:00 AM

**Linux/Mac Cron:**
```bash
# Edit crontab
crontab -e

# Add line (adjust path):
0 2 * * * /usr/bin/python3 /path/to/scripts/upload_eval_db.py
```

## Performance Optimization

### Data Caching
- Parquet files are automatically cached using `@st.cache_data`
- Navigation between alerts is fast after initial load
- Clear cache: Settings → Clear Cache in Streamlit UI

### Database Optimization
- Automatic indices on AICommentId, AlertId, CreatedAt
- SQLite database grows incrementally with evaluations
- Regular S3 backup preserves evaluation history

## Troubleshooting

### Common Issues

**"Import could not be resolved" errors:**
- These are linting warnings only
- Install dependencies: `pip install -r requirements.txt`
- Run app to verify everything works

**Data files not found:**
- Verify Parquet files are in `data/` folder
- Check file names match exactly (case-sensitive)
- App shows file status in sidebar

**Database errors:**
- Database auto-creates on first evaluation
- Check write permissions in `state/` folder
- Delete `state/eval.db` to reset (loses evaluations!)

### Performance Tips
- Use "Next Alert" button for efficient navigation
- Optional notes help track evaluation reasoning  
- Group similar comment types for consistent grading
- S3 sync runs in background (won't block app)

## Development Notes

### Key Components
- **schemas.py:** SQLModel classes for type safety
- **db.py:** Database operations with proper indexing
- **io.py:** Cached data loading with error handling
- **charts.py:** Plotly visualizations for context
- **Review page:** Main evaluation workflow with forms

### Extending the Application
- Add new chart types in `charts.py`
- Extend evaluation schema in `schemas.py` 
- Add new pages in `app/pages/`
- Modify grading scale in review form
- Add user authentication if needed

---

## ✅ You're Ready!

Your AI Comments Evaluator is now fully set up and ready to use. The application follows the architecture specified in your README and provides a complete evaluation workflow for AI-generated maintenance comments.

**Next Steps:**
1. Run the app: `streamlit run app/streamlit_app.py`
2. Start evaluating: Navigate to Review page
3. Configure S3 backup (optional): Set environment variables
4. Set up daily sync (optional): Configure cron/task scheduler