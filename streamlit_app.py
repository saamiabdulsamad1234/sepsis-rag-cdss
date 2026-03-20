import streamlit as st
import os
import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import plotly.graph_objects as go

#  Resolve project root so imports work regardless of CWD 
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

#  Page config (must be first Streamlit call) 
st.set_page_config(
    page_title="Sepsis Clinical Decision Support System",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 
#  CONFIGURATION — works on Cloud (st.secrets) or locally (.env)
# 
def _get_secret(key: str, default: str = "") -> str:
    """Fetch a config value from Streamlit secrets → env var → default."""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)

OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")
APP_PASSWORD   = _get_secret("APP_PASSWORD", "sepsis2024")
MAX_CALLS      = int(_get_secret("MAX_API_CALLS_PER_SESSION", "50"))

# Inject key into environment so LangChain / OpenAI pick it up
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# 
#  PASSWORD GATE
# 
def _check_password() -> bool:
    """Show a login screen; return True if authenticated."""
    if st.session_state.get("authenticated"):
        return True

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    *, *::before, *::after { font-family:'Inter',sans-serif!important; }
    .main { background:#0a0e1a; }
    .block-container { max-width:500px; padding-top:12vh; }
    #MainMenu,footer,header { visibility:hidden; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;margin-bottom:30px;">
        <div style="font-size:56px;margin-bottom:12px;"></div>
        <h1 style="color:#38bdf8;font-size:28px;font-weight:800;letter-spacing:1px;">
            Sepsis Clinical Decision Support
        </h1>
        <p style="color:#64748b;font-size:14px;">Enter the access code to continue</p>
    </div>
    """, unsafe_allow_html=True)

    pwd = st.text_input("Access Code", type="password", placeholder="Enter password…")
    if st.button("  Unlock", use_container_width=True, type="primary"):
        if pwd == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error(" Incorrect password")
    return False

# 
#  RATE LIMITER
# 
def _check_rate_limit() -> bool:
    """Increment API call counter; return True if under limit."""
    if "api_calls" not in st.session_state:
        st.session_state.api_calls = 0
    if st.session_state.api_calls >= MAX_CALLS:
        st.warning(
            f" You've reached the limit of **{MAX_CALLS} API calls** per session. "
            "Refresh the page to start a new session."
        )
        return False
    st.session_state.api_calls += 1
    return True

# 
#  INLINE RAG PIPELINE  (replaces the FastAPI backend)
# 
@st.cache_resource(show_spinner=" Initializing RAG engine…")
def _init_rag():
    """One-time initialisation of the RAG engine + index documents."""
    from rag_engine.pipeline import RAGPipeline
    from rag_engine.document_loader import DocumentLoader

    pipeline = RAGPipeline()

    #  Auto-index guidelines if the vector store is empty 
    guidelines_dir = PROJECT_ROOT / "data" / "guidelines"
    if not guidelines_dir.exists():
        # Create sample guidelines via the indexing script
        from scripts.index_documents import create_sample_guidelines
        create_sample_guidelines(str(guidelines_dir))

    collection_count = pipeline.vector_store.get_collection_count()
    if collection_count == 0:
        loader = DocumentLoader()
        docs = loader.load_directory(str(guidelines_dir))
        if docs:
            pipeline.vector_store.add_documents(docs)

    return pipeline

def _rag_analyze(pipeline, patient_data: dict) -> dict:
    """Run patient analysis through the RAG pipeline."""
    try:
        result = pipeline.analyze_patient(patient_data)
        return result
    except Exception as e:
        return {
            "summary": f"Analysis error: {str(e)}",
            "key_findings": [],
            "risk_factors": [],
            "recommendations": [],
            "urgency_level": "UNKNOWN",
            "reasoning": str(e),
        }

def _rag_chat(pipeline, patient_data: dict, question: str, history: list) -> dict:
    """Run chat through the RAG pipeline."""
    try:
        result = pipeline.chat(patient_data, question, history)
        return result
    except Exception as e:
        return {
            "answer": f"Sorry, I encountered an error: {str(e)}",
            "retrieved_documents": [],
            "reasoning_chain": [],
            "confidence": 0,
            "citations": [],
        }


# 
#  DEMO PATIENTS
# 
def _demo_patients() -> list:
    return [
        {
            "patient_id": "ICU-2024-001", "mrn": "MRN-847392", "age": 67, "gender": "Male",
            "admission_time": (datetime.now() - timedelta(hours=6)).isoformat(),
            "location": "ICU Bed 12A",
            "vitals": {"heart_rate":118,"systolic_bp":92,"diastolic_bp":58,"mean_arterial_pressure":69,"respiratory_rate":28,"temperature":38.8,"spo2":91},
            "labs": {"wbc":18500,"platelet_count":95000,"creatinine":2.4,"bilirubin":1.8,"lactate":3.2,"procalcitonin":8.5,"crp":185},
            "sofa_score": {"respiration":2,"coagulation":1,"liver":1,"cardiovascular":2,"cns":0,"renal":2,"total":8},
            "model_prediction": {"sepsis_probability":0.87,"risk_level":"HIGH","confidence":0.92,"feature_importance":{"lactate":0.18,"heart_rate":0.15,"sofa_total":0.14,"procalcitonin":0.12,"map":0.11}},
            "clinical_notes": "67M admitted from ED with suspected pneumonia. Increasing oxygen requirements. On 6L NC. Tachycardic, hypotensive. Lactate elevated. Broad-spectrum antibiotics initiated.",
            "orders": [
                {"time":"2 hours ago","order":"Blood cultures x2 STAT","status":"Completed"},
                {"time":"2 hours ago","order":"Vancomycin 1g IV","status":"Completed"},
                {"time":"2 hours ago","order":"Piperacillin-Tazobactam 4.5g IV","status":"Completed"},
                {"time":"1 hour ago","order":"Lactate level q4h","status":"Pending"},
                {"time":"30 min ago","order":"Fluid bolus 1L NS","status":"In Progress"},
            ],
        },
        {
            "patient_id": "ICU-2024-002", "mrn": "MRN-923847", "age": 54, "gender": "Female",
            "admission_time": (datetime.now() - timedelta(hours=12)).isoformat(),
            "location": "ICU Bed 08B",
            "vitals": {"heart_rate":105,"systolic_bp":108,"diastolic_bp":68,"mean_arterial_pressure":81,"respiratory_rate":22,"temperature":38.2,"spo2":94},
            "labs": {"wbc":14200,"platelet_count":145000,"creatinine":1.3,"bilirubin":1.1,"lactate":2.1,"procalcitonin":3.2,"crp":98},
            "sofa_score": {"respiration":1,"coagulation":0,"liver":0,"cardiovascular":1,"cns":0,"renal":1,"total":3},
            "model_prediction": {"sepsis_probability":0.58,"risk_level":"MODERATE","confidence":0.78,"feature_importance":{"heart_rate":0.16,"procalcitonin":0.14,"wbc":0.13,"lactate":0.12,"temperature":0.11}},
            "clinical_notes": "54F with UTI symptoms. Fever and flank pain. Urine culture pending. Responsive to fluids.",
            "orders": [
                {"time":"6 hours ago","order":"Urine culture","status":"Pending"},
                {"time":"6 hours ago","order":"Ceftriaxone 1g IV","status":"Completed"},
                {"time":"4 hours ago","order":"Fluid bolus 500ml","status":"Completed"},
            ],
        },
        {
            "patient_id": "ICU-2024-003", "mrn": "MRN-741852", "age": 72, "gender": "Male",
            "admission_time": (datetime.now() - timedelta(hours=18)).isoformat(),
            "location": "ICU Bed 15C",
            "vitals": {"heart_rate":135,"systolic_bp":78,"diastolic_bp":45,"mean_arterial_pressure":56,"respiratory_rate":32,"temperature":39.5,"spo2":87},
            "labs": {"wbc":24800,"platelet_count":62000,"creatinine":3.8,"bilirubin":3.2,"lactate":5.8,"procalcitonin":18.7,"crp":285},
            "sofa_score": {"respiration":3,"coagulation":2,"liver":2,"cardiovascular":3,"cns":1,"renal":3,"total":14},
            "model_prediction": {"sepsis_probability":0.96,"risk_level":"CRITICAL","confidence":0.97,"feature_importance":{"lactate":0.22,"sofa_total":0.19,"map":0.16,"procalcitonin":0.14,"platelet_count":0.12}},
            "clinical_notes": "72M in septic shock. On norepinephrine 0.15mcg/kg/min. Suspected intra-abdominal source. CT shows possible bowel perforation. Surgery consulted.",
            "orders": [
                {"time":"12 hours ago","order":"Norepinephrine gtt","status":"Active"},
                {"time":"10 hours ago","order":"CT abdomen/pelvis","status":"Completed"},
                {"time":"8 hours ago","order":"Surgical consult","status":"Completed"},
                {"time":"2 hours ago","order":"Vasopressin gtt","status":"Active"},
            ],
        },
    ]


# 
#  CSS  (same Epic-style dark theme from local version)
# 
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*,*::before,*::after{font-family:'Inter',sans-serif!important}
.main{background:#0a0e1a}
.block-container{padding-top:1rem;max-width:1400px}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0d1321 0%,#131a2e 100%);border-right:1px solid rgba(99,179,237,.15)}
section[data-testid="stSidebar"] *{color:#c9d1d9!important}
/* System Bar */
.system-bar{background:linear-gradient(135deg,#0f172a,#1e293b);border:1px solid rgba(56,189,248,.2);border-radius:12px;padding:14px 24px;display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;box-shadow:0 4px 24px rgba(0,0,0,.4)}
.system-bar .sys-title{font-size:18px;font-weight:700;color:#38bdf8;letter-spacing:1.5px;text-transform:uppercase}
.system-bar .sys-meta{font-size:13px;color:#94a3b8;display:flex;gap:20px;align-items:center}
.system-bar .sys-meta .live-dot{width:8px;height:8px;background:#22c55e;border-radius:50%;display:inline-block;margin-right:6px;animation:pulse-dot 2s infinite}
@keyframes pulse-dot{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(34,197,94,.7)}50%{opacity:.7;box-shadow:0 0 0 6px rgba(34,197,94,0)}}
/* Patient Banner */
.patient-banner{background:linear-gradient(135deg,#1e293b,#0f172a);border:1px solid rgba(56,189,248,.2);border-radius:12px;padding:20px 28px;margin-bottom:16px;box-shadow:0 4px 24px rgba(0,0,0,.3);display:flex;justify-content:space-between;align-items:center}
.patient-banner .pt-info{display:flex;align-items:center;gap:20px}
.patient-banner .pt-avatar{width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;color:white}
.patient-banner .pt-details h2{margin:0;font-size:22px;font-weight:700;color:#f1f5f9;letter-spacing:.5px}
.patient-banner .pt-details .pt-meta{font-size:13px;color:#94a3b8;margin-top:4px}
.patient-banner .pt-details .pt-meta span{margin-right:16px}
.risk-badge{padding:10px 24px;border-radius:8px;font-size:15px;font-weight:700;letter-spacing:1px;text-transform:uppercase;text-align:center;min-width:180px}
.risk-badge .risk-prob{font-size:12px;font-weight:400;opacity:.85;margin-top:4px;letter-spacing:0;text-transform:none}
.risk-critical{background:linear-gradient(135deg,#dc2626,#b91c1c);color:white;border:1px solid #ef4444;box-shadow:0 0 20px rgba(220,38,38,.3)}
.risk-high{background:linear-gradient(135deg,#ea580c,#c2410c);color:white;border:1px solid #f97316;box-shadow:0 0 20px rgba(234,88,12,.3)}
.risk-moderate{background:linear-gradient(135deg,#d97706,#b45309);color:white;border:1px solid #f59e0b;box-shadow:0 0 20px rgba(217,119,6,.3)}
.risk-low{background:linear-gradient(135deg,#16a34a,#15803d);color:white;border:1px solid #22c55e;box-shadow:0 0 20px rgba(22,163,74,.3)}
/* Panels */
.panel{background:linear-gradient(135deg,#1e293b,#0f172a);border:1px solid rgba(56,189,248,.12);border-radius:12px;padding:20px;margin-bottom:12px;box-shadow:0 2px 16px rgba(0,0,0,.2)}
.panel-header{font-size:14px;font-weight:600;color:#38bdf8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid rgba(56,189,248,.15);display:flex;align-items:center;gap:8px}
/* Vital Cards */
.vital-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}
.vital-card{background:rgba(15,23,42,.6);border:1px solid rgba(56,189,248,.1);border-radius:10px;padding:14px;text-align:center;transition:all .3s ease}
.vital-card:hover{border-color:rgba(56,189,248,.3);box-shadow:0 0 15px rgba(56,189,248,.1);transform:translateY(-2px)}
.vital-card .vital-label{font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}
.vital-card .vital-value{font-size:26px;font-weight:700;margin-bottom:2px}
.vital-card .vital-unit{font-size:11px;color:#64748b}
.vital-normal{color:#22c55e;border-left:3px solid #22c55e}
.vital-warning{color:#f59e0b;border-left:3px solid #f59e0b}
.vital-danger{color:#ef4444;border-left:3px solid #ef4444}
/* SOFA */
.sofa-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.sofa-item{background:rgba(15,23,42,.6);border-radius:8px;padding:12px;text-align:center;border:1px solid rgba(56,189,248,.1)}
.sofa-item .sofa-label{font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px}
.sofa-item .sofa-score{font-size:28px;font-weight:800;margin:4px 0}
.sofa-item .sofa-max{font-size:11px;color:#475569}
.sofa-0{color:#22c55e}.sofa-1{color:#84cc16}.sofa-2{color:#f59e0b}.sofa-3{color:#f97316}.sofa-4{color:#ef4444}
/* Clinical note */
.clinical-note{background:rgba(15,23,42,.6);border:1px solid rgba(56,189,248,.1);border-left:3px solid #38bdf8;border-radius:8px;padding:16px 20px;color:#cbd5e1;font-size:14px;line-height:1.7}
/* Analysis cards */
.finding-card{background:rgba(15,23,42,.6);border:1px solid rgba(56,189,248,.1);border-left:3px solid #f59e0b;border-radius:8px;padding:12px 16px;margin-bottom:8px;color:#e2e8f0;font-size:14px;transition:all .2s ease}
.finding-card:hover{background:rgba(15,23,42,.8)}
.risk-card{background:rgba(15,23,42,.6);border:1px solid rgba(239,68,68,.2);border-left:3px solid #ef4444;border-radius:8px;padding:12px 16px;margin-bottom:8px;color:#e2e8f0;font-size:14px}
.rec-card{background:rgba(15,23,42,.6);border:1px solid rgba(34,197,94,.2);border-left:3px solid #22c55e;border-radius:8px;padding:12px 16px;margin-bottom:8px;color:#e2e8f0;font-size:14px}
/* Alerts */
.alert-critical{background:linear-gradient(135deg,rgba(220,38,38,.15),rgba(185,28,28,.15));border:1px solid rgba(239,68,68,.4);color:#fca5a5;padding:16px 20px;border-radius:10px;font-weight:600;font-size:15px;margin-bottom:16px;display:flex;align-items:center;gap:10px}
.alert-high{background:linear-gradient(135deg,rgba(234,88,12,.15),rgba(194,65,12,.15));border:1px solid rgba(249,115,22,.4);color:#fdba74;padding:16px 20px;border-radius:10px;font-weight:600;font-size:15px;margin-bottom:16px}
.alert-moderate{background:linear-gradient(135deg,rgba(217,119,6,.15),rgba(180,83,9,.15));border:1px solid rgba(245,158,11,.4);color:#fcd34d;padding:16px 20px;border-radius:10px;font-weight:600;font-size:15px;margin-bottom:16px}
/* Timeline */
.timeline-entry{display:flex;gap:16px;padding:14px 0;border-bottom:1px solid rgba(56,189,248,.08)}
.timeline-entry:last-child{border-bottom:none}
.timeline-dot{width:12px;height:12px;border-radius:50%;margin-top:4px;flex-shrink:0}
.timeline-content .tl-order{color:#e2e8f0;font-size:14px;font-weight:500}
.timeline-content .tl-meta{color:#64748b;font-size:12px;margin-top:2px}
.dot-completed{background:#22c55e;box-shadow:0 0 8px rgba(34,197,94,.5)}
.dot-active{background:#3b82f6;box-shadow:0 0 8px rgba(59,130,246,.5);animation:pulse-dot 2s infinite}
.dot-pending{background:#64748b}
.dot-inprogress{background:#f59e0b;box-shadow:0 0 8px rgba(245,158,11,.5)}
/* Lab rows */
.lab-row{display:flex;justify-content:space-between;align-items:center;padding:10px 16px;border-radius:8px;margin-bottom:4px;font-size:14px}
.lab-row:nth-child(odd){background:rgba(15,23,42,.4)}
.lab-row .lab-name{color:#94a3b8;font-weight:500;min-width:140px}
.lab-row .lab-val{color:#f1f5f9;font-weight:700;font-size:16px;min-width:100px;text-align:right}
.lab-row .lab-unit{color:#64748b;font-size:12px;min-width:80px;text-align:right}
.lab-row .lab-ref{color:#475569;font-size:12px;min-width:120px;text-align:right}
.lab-abnormal .lab-val{color:#ef4444}
.lab-row .lab-flag{font-size:11px;font-weight:700;padding:2px 8px;border-radius:4px;min-width:40px;text-align:center}
.flag-high{background:rgba(239,68,68,.2);color:#ef4444}
.flag-low{background:rgba(59,130,246,.2);color:#60a5fa}
.flag-ok{color:transparent}
/* Welcome */
.welcome-screen{text-align:center;padding:80px 20px}
.welcome-screen .welcome-icon{font-size:64px;margin-bottom:20px}
.welcome-screen h1{color:#38bdf8;font-size:36px;font-weight:800;letter-spacing:1px;margin-bottom:12px}
.welcome-screen p{color:#64748b;font-size:16px}
.welcome-screen .welcome-features{display:flex;justify-content:center;gap:24px;margin-top:40px;flex-wrap:wrap}
.welcome-screen .feature-box{background:linear-gradient(135deg,#1e293b,#0f172a);border:1px solid rgba(56,189,248,.15);border-radius:12px;padding:24px;width:200px;transition:all .3s ease}
.welcome-screen .feature-box:hover{border-color:rgba(56,189,248,.4);transform:translateY(-4px);box-shadow:0 8px 24px rgba(0,0,0,.3)}
.welcome-screen .feature-box .feat-icon{font-size:28px;margin-bottom:10px}
.welcome-screen .feature-box .feat-title{color:#e2e8f0;font-weight:600;font-size:14px}
.welcome-screen .feature-box .feat-desc{color:#64748b;font-size:12px;margin-top:6px}
/* Sidebar */
.sidebar-stat{background:rgba(15,23,42,.6);border:1px solid rgba(56,189,248,.1);border-radius:8px;padding:12px;margin-bottom:8px;text-align:center}
.sidebar-stat .stat-label{font-size:10px;font-weight:600;color:#64748b!important;text-transform:uppercase;letter-spacing:1px}
.sidebar-stat .stat-value{font-size:24px;font-weight:800;margin:4px 0}
/* Rate limit */
.rate-badge{background:rgba(15,23,42,.6);border:1px solid rgba(56,189,248,.1);border-radius:8px;padding:8px;text-align:center;margin-top:8px}
.rate-badge .rate-label{font-size:10px;color:#64748b!important;text-transform:uppercase;letter-spacing:1px}
.rate-badge .rate-value{font-size:16px;font-weight:700;color:#38bdf8;margin-top:2px}
/* Tabs */
.stTabs [data-baseweb="tab-list"]{gap:0;background:rgba(15,23,42,.6);border-radius:10px;padding:4px;border:1px solid rgba(56,189,248,.1)}
.stTabs [data-baseweb="tab"]{border-radius:8px;color:#94a3b8;font-weight:500;font-size:13px;padding:8px 20px}
.stTabs [aria-selected="true"]{background:rgba(56,189,248,.15)!important;color:#38bdf8!important;border-bottom:none}
/* Misc */
#MainMenu,footer,header{visibility:hidden}
</style>
"""


# 
#  CHART HELPERS
# 
_CHART = dict(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,.6)", font=dict(family="Inter", color="#94a3b8"), margin=dict(l=40,r=20,t=50,b=40))

def _gauge(prob):
    fig = go.Figure(go.Indicator(mode="gauge+number", value=prob*100, number=dict(suffix="%",font=dict(size=42,color="#f1f5f9")), title=dict(text="Sepsis Probability",font=dict(size=14,color="#64748b")),
        gauge=dict(axis=dict(range=[0,100],tickwidth=1,tickcolor="#334155",dtick=20),bar=dict(color="#38bdf8",thickness=.3),bgcolor="rgba(15,23,42,.6)",borderwidth=0,
            steps=[dict(range=[0,30],color="rgba(34,197,94,.2)"),dict(range=[30,60],color="rgba(245,158,11,.2)"),dict(range=[60,80],color="rgba(249,115,22,.2)"),dict(range=[80,100],color="rgba(239,68,68,.2)")],
            threshold=dict(line=dict(color="#ef4444",width=3),thickness=.8,value=80))))
    fig.update_layout(**_CHART, height=280)
    return fig

def _feat_chart(features):
    df = pd.DataFrame(list(features.items()), columns=['Feature','Importance']).sort_values('Importance')
    colors = ['#38bdf8' if v<.15 else '#f59e0b' if v<.18 else '#ef4444' for v in df['Importance']]
    fig = go.Figure(go.Bar(y=df['Feature'],x=df['Importance'],orientation='h',marker=dict(color=colors,line=dict(width=0)),text=[f"{x:.0%}" for x in df['Importance']],textposition='outside',textfont=dict(color="#94a3b8",size=11)))
    fig.update_layout(**_CHART,height=280,title=dict(text="Feature Importance",font=dict(size=14,color="#64748b")),xaxis=dict(showgrid=False,zeroline=False,showticklabels=False),yaxis=dict(showgrid=False))
    return fig


# 
#  RENDERING HELPERS
# 
_VITAL_RANGES = {'heart_rate':(60,100),'systolic_bp':(90,120),'diastolic_bp':(60,80),'mean_arterial_pressure':(65,110),'respiratory_rate':(12,20),'temperature':(36.5,37.5),'spo2':(95,100)}
_VITAL_LABELS = {'heart_rate':('HR','bpm'),'systolic_bp':('SBP','mmHg'),'diastolic_bp':('DBP','mmHg'),'mean_arterial_pressure':('MAP','mmHg'),'respiratory_rate':('RR','/min'),'temperature':('Temp','°C'),'spo2':('SpO₂','%')}

def _vs(key,val):
    lo,hi=_VITAL_RANGES.get(key,(0,9999))
    if val<lo*.85 or val>hi*1.15: return 'vital-danger'
    if val<lo or val>hi: return 'vital-warning'
    return 'vital-normal'

def _render_vitals(v):
    c=""
    for k in ['heart_rate','systolic_bp','diastolic_bp','mean_arterial_pressure','respiratory_rate','temperature','spo2']:
        val=v[k]; l,u=_VITAL_LABELS[k]; s=_vs(k,val); f=f"{val:.1f}" if k=='temperature' else f"{val:.0f}"
        c+=f'<div class="vital-card {s}"><div class="vital-label">{l}</div><div class="vital-value">{f}</div><div class="vital-unit">{u}</div></div>'
    st.markdown(f'<div class="vital-grid">{c}</div>',unsafe_allow_html=True)

def _render_sofa(s):
    p=""
    for k in ['respiration','coagulation','liver','cardiovascular','cns','renal']:
        v=s[k]; p+=f'<div class="sofa-item"><div class="sofa-label">{k.title()}</div><div class="sofa-score sofa-{v}">{v}</div><div class="sofa-max">/ 4</div></div>'
    st.markdown(f'<div class="sofa-grid">{p}</div>',unsafe_allow_html=True)

_LAB_CFG=[('wbc','WBC','cells/μL',4000,11000,'4,000–11,000'),('platelet_count','Platelets','×10³/μL',150000,400000,'150,000–400,000'),('creatinine','Creatinine','mg/dL',.6,1.2,'0.6–1.2'),('bilirubin','Bilirubin','mg/dL',.1,1.2,'0.1–1.2'),('lactate','Lactate','mmol/L',0,2,'<2.0'),('procalcitonin','Procalcitonin','ng/mL',0,.5,'<0.5'),('crp','CRP','mg/L',0,10,'<10')]

def _render_labs(labs):
    r=""
    for key,name,unit,lo,hi,ref in _LAB_CFG:
        val=labs[key]; ab=val<lo or val>hi; flag="H" if val>hi else ("L" if val<lo else ""); fc="flag-high" if val>hi else ("flag-low" if val<lo else "flag-ok"); rc="lab-abnormal" if ab else ""
        fmt=f"{val:,.0f}" if key in ('wbc','platelet_count') else (f"{val:.0f}" if key=='crp' else f"{val:.1f}")
        r+=f'<div class="lab-row {rc}"><span class="lab-name">{name}</span><span class="lab-val">{fmt}</span><span class="lab-unit">{unit}</span><span class="lab-ref">{ref}</span><span class="lab-flag {fc}">{flag}</span></div>'
    st.markdown(f'<div class="panel">{r}</div>',unsafe_allow_html=True)

def _render_timeline(orders):
    e=""
    for o in orders:
        dc={'Completed':'dot-completed','Active':'dot-active','In Progress':'dot-inprogress','Pending':'dot-pending'}.get(o['status'],'dot-pending')
        sc={'Completed':'#22c55e','Active':'#3b82f6','In Progress':'#f59e0b','Pending':'#64748b'}.get(o['status'],'#64748b')
        e+=f'<div class="timeline-entry"><div class="timeline-dot {dc}"></div><div class="timeline-content"><div class="tl-order">{o["order"]}</div><div class="tl-meta">{o["time"]} · <span style="color:{sc}">{o["status"]}</span></div></div></div>'
    st.markdown(f'<div class="panel">{e}</div>',unsafe_allow_html=True)


# 
#  MAIN
# 
def main():
    #  Password gate 
    if not _check_password():
        return

    #  CSS 
    st.markdown(_CSS, unsafe_allow_html=True)

    #  Session state 
    for k, v in {"chat_history": [], "current_patient": None, "analysis_result": None, "api_calls": 0}.items():
        if k not in st.session_state:
            st.session_state[k] = v

    #  Init RAG pipeline (cached) 
    rag_ready = False
    pipeline = None
    if OPENAI_API_KEY:
        try:
            pipeline = _init_rag()
            rag_ready = True
        except Exception as e:
            st.sidebar.error(f"RAG init error: {e}")

    #  Sidebar 
    with st.sidebar:
        st.markdown("###  Command Center")
        st.markdown("---")

        status_color = "#22c55e" if rag_ready else "#ef4444"
        status_text  = "ONLINE" if rag_ready else "NO API KEY"
        st.markdown(f"""
        <div class="sidebar-stat">
            <div class="stat-label">System Status</div>
            <div class="stat-value" style="color:{status_color};">  {status_text}</div>
        </div>
        """, unsafe_allow_html=True)

        remaining = max(0, MAX_CALLS - st.session_state.get("api_calls", 0))
        st.markdown(f"""
        <div class="rate-badge">
            <div class="rate-label">API Calls Remaining</div>
            <div class="rate-value">{remaining} / {MAX_CALLS}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("##### Patient Selection")

        patients = _demo_patients()
        p_map = {p["patient_id"]: p for p in patients}
        icons = {"HIGH":"","MODERATE":"","CRITICAL":"","LOW":""}
        sel = st.selectbox("Select Patient", list(p_map.keys()),
            format_func=lambda x: f"{icons.get(p_map[x]['model_prediction']['risk_level'],'')} {x} — {p_map[x]['age']}yo {p_map[x]['gender'][0]}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button(" Load", use_container_width=True):
                st.session_state.current_patient = p_map[sel]
                st.session_state.analysis_result = None
                st.session_state.chat_history = []
                st.rerun()
        with c2:
            if st.button(" Clear", use_container_width=True):
                st.session_state.current_patient = None
                st.session_state.analysis_result = None
                st.session_state.chat_history = []
                st.rerun()

        if st.session_state.current_patient:
            p = st.session_state.current_patient
            st.markdown("---")
            st.markdown("##### Quick Indicators")
            sc = '#22c55e' if p['sofa_score']['total']<6 else '#f59e0b' if p['sofa_score']['total']<10 else '#ef4444'
            lc = '#22c55e' if p['labs']['lactate']<2 else '#f59e0b' if p['labs']['lactate']<4 else '#ef4444'
            mc = '#22c55e' if p['vitals']['mean_arterial_pressure']>=65 else '#ef4444'
            st.markdown(f"""
            <div class="sidebar-stat"><div class="stat-label">SOFA Score</div><div class="stat-value" style="color:{sc};">{p['sofa_score']['total']}<span style="font-size:14px;color:#475569;">/24</span></div></div>
            <div class="sidebar-stat"><div class="stat-label">Lactate</div><div class="stat-value" style="color:{lc};">{p['labs']['lactate']}<span style="font-size:14px;color:#475569;"> mmol/L</span></div></div>
            <div class="sidebar-stat"><div class="stat-label">MAP</div><div class="stat-value" style="color:{mc};">{p['vitals']['mean_arterial_pressure']:.0f}<span style="font-size:14px;color:#475569;"> mmHg</span></div></div>
            """, unsafe_allow_html=True)

    #  System bar 
    now_str = datetime.now().strftime("%b %d, %Y  %H:%M")
    st.markdown(f"""
    <div class="system-bar">
        <div class="sys-title"> Sepsis Clinical Decision Support</div>
        <div class="sys-meta">
            <span><span class="live-dot"></span>LIVE</span>
            <span>⏱ {now_str}</span>
            <span>v2.0</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    #  Welcome screen 
    if not st.session_state.current_patient:
        st.markdown("""
        <div class="welcome-screen">
            <div class="welcome-icon"></div>
            <h1>Sepsis Clinical Decision Support</h1>
            <p>AI-powered clinical analysis with evidence-based guideline retrieval</p>
            <div class="welcome-features">
                <div class="feature-box"><div class="feat-icon"></div><div class="feat-title">Real-Time Monitoring</div><div class="feat-desc">Vitals, labs & SOFA scoring</div></div>
                <div class="feature-box"><div class="feat-icon"></div><div class="feat-title">AI Analysis</div><div class="feat-desc">RAG-powered clinical reasoning</div></div>
                <div class="feature-box"><div class="feat-icon"></div><div class="feat-title">Clinical Chat</div><div class="feat-desc">Evidence-based Q&A assistant</div></div>
                <div class="feature-box"><div class="feat-icon"></div><div class="feat-title">Order Tracking</div><div class="feat-desc">Clinical timeline & history</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    patient = st.session_state.current_patient

    #  Patient banner 
    risk = patient['model_prediction']['risk_level']
    risk_cls = f"risk-{risk.lower()}"
    avatar_bg = {'CRITICAL':'#dc2626','HIGH':'#ea580c','MODERATE':'#d97706','LOW':'#16a34a'}.get(risk,'#64748b')
    initials = f"{patient['gender'][0]}{patient['age']}"
    adm = datetime.fromisoformat(patient['admission_time'])
    los_h = int((datetime.now()-adm).total_seconds()/3600)

    st.markdown(f"""
    <div class="patient-banner">
        <div class="pt-info">
            <div class="pt-avatar" style="background:{avatar_bg};">{initials}</div>
            <div class="pt-details">
                <h2>{patient['patient_id']}</h2>
                <div class="pt-meta">
                    <span> {patient.get('location','ICU')}</span>
                    <span> {patient.get('mrn','N/A')}</span>
                    <span> LOS: {los_h}h</span>
                    <span> {patient['age']}yo {patient['gender']}</span>
                </div>
            </div>
        </div>
        <div class="risk-badge {risk_cls}">
            {risk} RISK
            <div class="risk-prob">{patient['model_prediction']['sepsis_probability']:.0%} probability · {patient['model_prediction']['confidence']:.0%} confidence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    #  Tabs 
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["  Monitoring","  AI Analysis","  Clinical Chat","  Laboratory","  Orders"])

    with tab1:
        st.markdown('<div class="panel-header"> Vital Signs</div>', unsafe_allow_html=True)
        _render_vitals(patient['vitals'])
        st.markdown("")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="panel-header"> Sepsis Risk Assessment</div>', unsafe_allow_html=True)
            st.plotly_chart(_gauge(patient['model_prediction']['sepsis_probability']), use_container_width=True)
        with c2:
            st.markdown('<div class="panel-header"> Model Feature Importance</div>', unsafe_allow_html=True)
            st.plotly_chart(_feat_chart(patient['model_prediction']['feature_importance']), use_container_width=True)
        st.markdown("")
        c3, c4 = st.columns(2)
        with c3:
            st.markdown(f'<div class="panel-header"> SOFA Score — Total: {patient["sofa_score"]["total"]}/24</div>', unsafe_allow_html=True)
            _render_sofa(patient['sofa_score'])
        with c4:
            st.markdown('<div class="panel-header"> Clinical Notes</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="clinical-note">{patient.get("clinical_notes","No notes available")}</div>', unsafe_allow_html=True)

    with tab2:
        c_b1,c_b2,_ = st.columns([1,1,4])
        with c_b1:
            run_analysis = st.button("  Generate Analysis", type="primary", use_container_width=True)
        with c_b2:
            if st.button("  Clear", use_container_width=True, key="clear_analysis"):
                st.session_state.analysis_result = None

        if run_analysis and pipeline:
            if _check_rate_limit():
                with st.spinner(" Running AI analysis with clinical guidelines…"):
                    result = _rag_analyze(pipeline, patient)
                if result:
                    st.session_state.analysis_result = result
                    st.rerun()
        elif run_analysis and not pipeline:
            st.error(" RAG engine not available. Check your OpenAI API key.")

        if st.session_state.analysis_result:
            analysis = st.session_state.analysis_result
            urgency = analysis.get('urgency_level','MODERATE')
            alert_cls = {'CRITICAL':'alert-critical','HIGH':'alert-high'}.get(urgency,'alert-moderate')
            urgency_icon = {'CRITICAL':'','HIGH':''}.get(urgency,'ℹ')
            st.markdown(f'<div class="{alert_cls}">{urgency_icon} URGENCY LEVEL: {urgency}</div>', unsafe_allow_html=True)
            cf, cr = st.columns(2)
            with cf:
                st.markdown('<div class="panel-header"> Key Findings</div>', unsafe_allow_html=True)
                for f in analysis.get('key_findings',[]):
                    st.markdown(f'<div class="finding-card"> {f}</div>', unsafe_allow_html=True)
            with cr:
                st.markdown('<div class="panel-header"> Risk Factors</div>', unsafe_allow_html=True)
                for r in analysis.get('risk_factors',[]):
                    st.markdown(f'<div class="risk-card"> {r}</div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-header"> Evidence-Based Recommendations</div>', unsafe_allow_html=True)
            for i, rec in enumerate(analysis.get('recommendations',[]),1):
                st.markdown(f'<div class="rec-card"><strong>{i}.</strong> {rec}</div>', unsafe_allow_html=True)
            with st.expander(" View Full Clinical Reasoning Chain"):
                st.markdown(f'<div class="clinical-note">{analysis.get("reasoning","No reasoning available")}</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="panel-header"> Clinical Decision Support Chat</div>', unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        if prompt := st.chat_input("Ask about this patient's clinical presentation…"):
            st.session_state.chat_history.append({"role":"user","content":prompt})
            with st.chat_message("user"):
                st.write(prompt)
            with st.chat_message("assistant"):
                if pipeline and _check_rate_limit():
                    with st.spinner(" Searching clinical guidelines…"):
                        resp = _rag_chat(pipeline, patient, prompt, st.session_state.chat_history[:-1])
                    if resp:
                        st.write(resp["answer"])
                        with st.expander(" Retrieved Clinical Guidelines"):
                            for i, doc in enumerate(resp.get("retrieved_documents",[]),1):
                                st.markdown(f"**Source {i}: {doc['source']}** (Relevance: {doc['relevance_score']:.2f})")
                                st.text(doc['content'][:400]+"…")
                                st.markdown("---")
                        with st.expander(" Reasoning Steps"):
                            for i, step in enumerate(resp.get("reasoning_chain",[]),1):
                                st.markdown(f"{i}. {step}")
                        st.session_state.chat_history.append({"role":"assistant","content":resp["answer"]})
                elif not pipeline:
                    st.error(" RAG engine not available.")

    with tab4:
        st.markdown('<div class="panel-header"> Complete Laboratory Panel</div>', unsafe_allow_html=True)
        _render_labs(patient['labs'])

    with tab5:
        st.markdown('<div class="panel-header"> Clinical Orders & Timeline</div>', unsafe_allow_html=True)
        if patient.get('orders'):
            _render_timeline(patient['orders'])
        else:
            st.info("No orders recorded for this patient")


if __name__ == "__main__":
    main()
