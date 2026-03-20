from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class VitalSigns(BaseModel):
    heart_rate: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    mean_arterial_pressure: Optional[float] = None
    respiratory_rate: Optional[float] = None
    temperature: Optional[float] = None
    spo2: Optional[float] = None

class LabResults(BaseModel):
    wbc: Optional[float] = None
    platelet_count: Optional[float] = None
    creatinine: Optional[float] = None
    bilirubin: Optional[float] = None
    lactate: Optional[float] = None
    procalcitonin: Optional[float] = None
    crp: Optional[float] = None

class SOFAScore(BaseModel):
    respiration: int = Field(ge=0, le=4)
    coagulation: int = Field(ge=0, le=4)
    liver: int = Field(ge=0, le=4)
    cardiovascular: int = Field(ge=0, le=4)
    cns: int = Field(ge=0, le=4)
    renal: int = Field(ge=0, le=4)
    total: int = Field(ge=0, le=24)

class ModelPrediction(BaseModel):
    sepsis_probability: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    feature_importance: Dict[str, float] = {}

class PatientContext(BaseModel):
    patient_id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    admission_time: Optional[datetime] = None
    vitals: VitalSigns
    labs: LabResults
    sofa_score: SOFAScore
    model_prediction: ModelPrediction
    clinical_notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatRequest(BaseModel):
    patient_context: PatientContext
    question: str
    chat_history: List[ChatMessage] = []

class RetrievedDocument(BaseModel):
    content: str
    source: str
    relevance_score: float
    metadata: Dict[str, Any] = {}

class ChatResponse(BaseModel):
    answer: str
    retrieved_documents: List[RetrievedDocument]
    reasoning_chain: List[str]
    confidence: float
    citations: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)

class AnalysisRequest(BaseModel):
    patient_context: PatientContext

class AnalysisResponse(BaseModel):
    summary: str
    key_findings: List[str]
    risk_factors: List[str]
    recommendations: List[str]
    urgency_level: str
    reasoning: str
