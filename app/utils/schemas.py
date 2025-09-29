"""
Data schemas and dataclasses for oil analysis evaluator.
Defines the evaluations table structure and validation models.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class Evaluation:
    """
    Dataclass for storing AI comment evaluations.
    One row = one evaluator's grade for one AI comment tied to a specific AlertId.
    """
    AICommentId: str          # Required - links to ai_comments.parquet
    AlertId: str              # Required - links to alerts.parquet
    Grade: int                # Required - grade between 1-7
    UserId: Optional[str] = None      # Optional evaluator identifier
    Notes: Optional[str] = None       # Optional free-text notes
    CreatedAt: Optional[datetime] = None  # Timestamp (set automatically)
    EvaluationId: Optional[int] = None    # Primary key (set by database)
    
    def __post_init__(self):
        """Set default values after initialization"""
        if self.CreatedAt is None:
            self.CreatedAt = datetime.utcnow()
        
        # Validate grade range
        if not (1 <= self.Grade <= 7):
            raise ValueError(f"Grade must be between 1-7, got {self.Grade}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Evaluation':
        """Create instance from dictionary"""
        # Handle datetime conversion if it's a string
        if 'CreatedAt' in data and isinstance(data['CreatedAt'], str):
            data['CreatedAt'] = datetime.fromisoformat(data['CreatedAt'])
        return cls(**data)


@dataclass
class EvaluationCreate:
    """Schema for creating new evaluations"""
    AICommentId: str
    AlertId: str
    Grade: int
    UserId: Optional[str] = None
    Notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate input data"""
        if not (1 <= self.Grade <= 7):
            raise ValueError(f"Grade must be between 1-7, got {self.Grade}")
    
    def to_evaluation(self) -> Evaluation:
        """Convert to full Evaluation object"""
        return Evaluation(
            AICommentId=self.AICommentId,
            AlertId=self.AlertId,
            Grade=self.Grade,
            UserId=self.UserId,
            Notes=self.Notes
        )


# Data models for parquet file structures (for type hints and validation)
@dataclass
class AlertData:
    """Schema matching alerts.parquet structure"""
    AlertId: str
    UnitId: str
    Component: str
    TimeStart: datetime
    OilAlertId: Optional[str] = None
    TelAlertId: Optional[str] = None
    Label: Optional[str] = None  # oil_only | telemetry_only | both


@dataclass
class OilMeasurement:
    """Schema matching oil_measurements.parquet structure"""
    OilAlertId: str
    SampleDate: datetime
    UnitId: str
    Component: str
    ElementName: str
    Value: float
    IsLimitReached: bool
    OilMeter: Optional[str] = None
    LimitValue: Optional[float] = None
    BreachLevel: Optional[str] = None  # none | alert | critical | urgent


@dataclass
class TelemetryMeasurement:
    """Schema matching telemetry_measurements.parquet structure"""
    TelAlertId: str
    Timestamp: datetime
    UnitId: str
    Component: str
    VariableName: str
    Value: float
    IsLimitReached: bool
    ComponentMeter: Optional[str] = None
    UpperLimitValue: Optional[float] = None
    LowerLimitValue: Optional[float] = None


@dataclass
class AIComment:
    """Schema matching ai_comments.parquet structure"""
    AICommentId: str
    AlertId: str
    CommentText: str
    CommentType: str  # baseline | prompt_v2 | rule_based | etc.


# SQL table creation statements
EVALUATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS evaluations (
    EvaluationId INTEGER PRIMARY KEY AUTOINCREMENT,
    AICommentId TEXT NOT NULL,
    AlertId TEXT NOT NULL,
    UserId TEXT,
    Grade INTEGER NOT NULL CHECK (Grade >= 1 AND Grade <= 7),
    Notes TEXT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Index creation statements for performance
EVALUATIONS_INDICES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_eval_comment ON evaluations(AICommentId);",
    "CREATE INDEX IF NOT EXISTS idx_eval_alert ON evaluations(AlertId);", 
    "CREATE INDEX IF NOT EXISTS idx_eval_created ON evaluations(CreatedAt);"
]