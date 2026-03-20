import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List
import time

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Sepsis Clinical Decision Support System",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)


# 
#  EPIC-STYLE CSS — Dark Clinical Theme
# 
def apply_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /*  Global Reset  */
    *, *::before, *::after { font-family: 'Inter', sans-serif !important; }

    .main { background: #0a0e1a; }
    .block-container { padding-top: 1rem; max-width: 1400px; }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1321 0%, #131a2e 100%);
        border-right: 1px solid rgba(99, 179, 237, 0.15);
    }
    section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

    /*  Top System Bar  */
    .system-bar {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 12px;
        padding: 14px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    }
    .system-bar .sys-title {
        font-size: 18px;
        font-weight: 700;
        color: #38bdf8;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }
    .system-bar .sys-meta {
        font-size: 13px;
        color: #94a3b8;
        display: flex;
        gap: 20px;
        align-items: center;
    }
    .system-bar .sys-meta .live-dot {
        width: 8px; height: 8px;
        background: #22c55e;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
        animation: pulse-dot 2s infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(34,197,94,0.7); }
        50% { opacity: 0.7; box-shadow: 0 0 0 6px rgba(34,197,94,0); }
    }

    /*  Patient ADT Banner  */
    .patient-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 12px;
        padding: 20px 28px;
        margin-bottom: 16px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .patient-banner .pt-info {
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .patient-banner .pt-avatar {
        width: 56px; height: 56px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        font-weight: 700;
        color: white;
    }
    .patient-banner .pt-details h2 {
        margin: 0;
        font-size: 22px;
        font-weight: 700;
        color: #f1f5f9;
        letter-spacing: 0.5px;
    }
    .patient-banner .pt-details .pt-meta {
        font-size: 13px;
        color: #94a3b8;
        margin-top: 4px;
    }
    .patient-banner .pt-details .pt-meta span {
        margin-right: 16px;
    }
    .risk-badge {
        padding: 10px 24px;
        border-radius: 8px;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        text-align: center;
        min-width: 180px;
    }
    .risk-badge .risk-prob {
        font-size: 12px;
        font-weight: 400;
        opacity: 0.85;
        margin-top: 4px;
        letter-spacing: 0;
        text-transform: none;
    }
    .risk-critical { background: linear-gradient(135deg, #dc2626, #b91c1c); color: white; border: 1px solid #ef4444; box-shadow: 0 0 20px rgba(220,38,38,0.3); }
    .risk-high     { background: linear-gradient(135deg, #ea580c, #c2410c); color: white; border: 1px solid #f97316; box-shadow: 0 0 20px rgba(234,88,12,0.3); }
    .risk-moderate { background: linear-gradient(135deg, #d97706, #b45309); color: white; border: 1px solid #f59e0b; box-shadow: 0 0 20px rgba(217,119,6,0.3); }
    .risk-low      { background: linear-gradient(135deg, #16a34a, #15803d); color: white; border: 1px solid #22c55e; box-shadow: 0 0 20px rgba(22,163,74,0.3); }

    /*  Section Panels  */
    .panel {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(56, 189, 248, 0.12);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
        box-shadow: 0 2px 16px rgba(0,0,0,0.2);
    }
    .panel-header {
        font-size: 14px;
        font-weight: 600;
        color: #38bdf8;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 16px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(56, 189, 248, 0.15);
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /*  Vital Sign Cards  */
    .vital-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 10px;
    }
    .vital-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(56, 189, 248, 0.1);
        border-radius: 10px;
        padding: 14px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .vital-card:hover {
        border-color: rgba(56, 189, 248, 0.3);
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.1);
        transform: translateY(-2px);
    }
    .vital-card .vital-label {
        font-size: 11px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .vital-card .vital-value {
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 2px;
    }
    .vital-card .vital-unit {
        font-size: 11px;
        color: #64748b;
    }
    .vital-normal  { color: #22c55e; border-left: 3px solid #22c55e; }
    .vital-warning { color: #f59e0b; border-left: 3px solid #f59e0b; }
    .vital-danger  { color: #ef4444; border-left: 3px solid #ef4444; }

    /*  SOFA Breakdown  */
    .sofa-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
    }
    .sofa-item {
        background: rgba(15, 23, 42, 0.6);
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        border: 1px solid rgba(56, 189, 248, 0.1);
    }
    .sofa-item .sofa-label {
        font-size: 11px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .sofa-item .sofa-score {
        font-size: 28px;
        font-weight: 800;
        margin: 4px 0;
    }
    .sofa-item .sofa-max {
        font-size: 11px;
        color: #475569;
    }
    .sofa-0 { color: #22c55e; }
    .sofa-1 { color: #84cc16; }
    .sofa-2 { color: #f59e0b; }
    .sofa-3 { color: #f97316; }
    .sofa-4 { color: #ef4444; }

    /*  Clinical Notes  */
    .clinical-note {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(56, 189, 248, 0.1);
        border-left: 3px solid #38bdf8;
        border-radius: 8px;
        padding: 16px 20px;
        color: #cbd5e1;
        font-size: 14px;
        line-height: 1.7;
    }

    /*  Analysis Cards  */
    .finding-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(56, 189, 248, 0.1);
        border-left: 3px solid #f59e0b;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        color: #e2e8f0;
        font-size: 14px;
        transition: all 0.2s ease;
    }
    .finding-card:hover { background: rgba(15, 23, 42, 0.8); }
    .risk-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-left: 3px solid #ef4444;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        color: #e2e8f0;
        font-size: 14px;
    }
    .rec-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(34, 197, 94, 0.2);
        border-left: 3px solid #22c55e;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        color: #e2e8f0;
        font-size: 14px;
    }

    /*  Alert Banners  */
    .alert-critical {
        background: linear-gradient(135deg, rgba(220,38,38,0.15), rgba(185,28,28,0.15));
        border: 1px solid rgba(239, 68, 68, 0.4);
        color: #fca5a5;
        padding: 16px 20px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 15px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .alert-high {
        background: linear-gradient(135deg, rgba(234,88,12,0.15), rgba(194,65,12,0.15));
        border: 1px solid rgba(249, 115, 22, 0.4);
        color: #fdba74;
        padding: 16px 20px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 15px;
        margin-bottom: 16px;
    }
    .alert-moderate {
        background: linear-gradient(135deg, rgba(217,119,6,0.15), rgba(180,83,9,0.15));
        border: 1px solid rgba(245, 158, 11, 0.4);
        color: #fcd34d;
        padding: 16px 20px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 15px;
        margin-bottom: 16px;
    }

    /*  Timeline  */
    .timeline-entry {
        display: flex;
        gap: 16px;
        padding: 14px 0;
        border-bottom: 1px solid rgba(56, 189, 248, 0.08);
    }
    .timeline-entry:last-child { border-bottom: none; }
    .timeline-dot {
        width: 12px; height: 12px;
        border-radius: 50%;
        margin-top: 4px;
        flex-shrink: 0;
    }
    .timeline-content .tl-order {
        color: #e2e8f0;
        font-size: 14px;
        font-weight: 500;
    }
    .timeline-content .tl-meta {
        color: #64748b;
        font-size: 12px;
        margin-top: 2px;
    }
    .dot-completed  { background: #22c55e; box-shadow: 0 0 8px rgba(34,197,94,0.5); }
    .dot-active     { background: #3b82f6; box-shadow: 0 0 8px rgba(59,130,246,0.5); animation: pulse-dot 2s infinite; }
    .dot-pending    { background: #64748b; }
    .dot-inprogress { background: #f59e0b; box-shadow: 0 0 8px rgba(245,158,11,0.5); }

    /*  Lab Table  */
    .lab-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 16px;
        border-radius: 8px;
        margin-bottom: 4px;
        font-size: 14px;
    }
    .lab-row:nth-child(odd) { background: rgba(15, 23, 42, 0.4); }
    .lab-row .lab-name { color: #94a3b8; font-weight: 500; min-width: 140px; }
    .lab-row .lab-val  { color: #f1f5f9; font-weight: 700; font-size: 16px; min-width: 100px; text-align: right; }
    .lab-row .lab-unit { color: #64748b; font-size: 12px; min-width: 80px; text-align: right; }
    .lab-row .lab-ref  { color: #475569; font-size: 12px; min-width: 120px; text-align: right; }
    .lab-abnormal .lab-val { color: #ef4444; }
    .lab-row .lab-flag {
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        min-width: 40px;
        text-align: center;
    }
    .flag-high { background: rgba(239,68,68,0.2); color: #ef4444; }
    .flag-low  { background: rgba(59,130,246,0.2); color: #60a5fa; }
    .flag-ok   { color: transparent; }

    /*  Welcome Screen  */
    .welcome-screen {
        text-align: center;
        padding: 80px 20px;
    }
    .welcome-screen .welcome-icon {
        font-size: 64px;
        margin-bottom: 20px;
    }
    .welcome-screen h1 {
        color: #38bdf8;
        font-size: 36px;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 12px;
    }
    .welcome-screen p {
        color: #64748b;
        font-size: 16px;
    }
    .welcome-screen .welcome-features {
        display: flex;
        justify-content: center;
        gap: 24px;
        margin-top: 40px;
    }
    .welcome-screen .feature-box {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 1px solid rgba(56, 189, 248, 0.15);
        border-radius: 12px;
        padding: 24px;
        width: 200px;
        transition: all 0.3s ease;
    }
    .welcome-screen .feature-box:hover {
        border-color: rgba(56, 189, 248, 0.4);
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .welcome-screen .feature-box .feat-icon { font-size: 28px; margin-bottom: 10px; }
    .welcome-screen .feature-box .feat-title { color: #e2e8f0; font-weight: 600; font-size: 14px; }
    .welcome-screen .feature-box .feat-desc  { color: #64748b; font-size: 12px; margin-top: 6px; }

    /*  Sidebar Styling  */
    .sidebar-stat {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(56, 189, 248, 0.1);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        text-align: center;
    }
    .sidebar-stat .stat-label {
        font-size: 10px;
        font-weight: 600;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .sidebar-stat .stat-value {
        font-size: 24px;
        font-weight: 800;
        margin: 4px 0;
    }

    /*  Tabs Override  */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background: rgba(15, 23, 42, 0.6);
        border-radius: 10px;
        padding: 4px;
        border: 1px solid rgba(56, 189, 248, 0.1);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 500;
        font-size: 13px;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(56, 189, 248, 0.15) !important;
        color: #38bdf8 !important;
        border-bottom: none;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 16px;
    }

    /*  Plotly chart background  */
    .stPlotlyChart { border-radius: 12px; overflow: hidden; }

    /*  Hide streamlit branding  */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


# 
#  SESSION STATE
# 
def init_session_state():
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_patient' not in st.session_state:
        st.session_state.current_patient = None
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'selected_patient_id' not in st.session_state:
        st.session_state.selected_patient_id = None


# 
#  DEMO PATIENTS
# 
def get_demo_patients():
    return [
        {
            "patient_id": "ICU-2024-001",
            "mrn": "MRN-847392",
            "age": 67,
            "gender": "Male",
            "admission_time": (datetime.now() - timedelta(hours=6)).isoformat(),
            "location": "ICU Bed 12A",
            "vitals": {
                "heart_rate": 118.0, "systolic_bp": 92.0, "diastolic_bp": 58.0,
                "mean_arterial_pressure": 69.0, "respiratory_rate": 28.0,
                "temperature": 38.8, "spo2": 91.0
            },
            "labs": {
                "wbc": 18500.0, "platelet_count": 95000.0, "creatinine": 2.4,
                "bilirubin": 1.8, "lactate": 3.2, "procalcitonin": 8.5, "crp": 185.0
            },
            "sofa_score": {
                "respiration": 2, "coagulation": 1, "liver": 1,
                "cardiovascular": 2, "cns": 0, "renal": 2, "total": 8
            },
            "model_prediction": {
                "sepsis_probability": 0.87, "risk_level": "HIGH", "confidence": 0.92,
                "feature_importance": {
                    "lactate": 0.18, "heart_rate": 0.15, "sofa_total": 0.14,
                    "procalcitonin": 0.12, "map": 0.11
                }
            },
            "clinical_notes": "67M admitted from ED with suspected pneumonia. Increasing oxygen requirements. On 6L NC. Tachycardic, hypotensive. Lactate elevated. Broad-spectrum antibiotics initiated.",
            "orders": [
                {"time": "2 hours ago", "order": "Blood cultures x2 STAT", "status": "Completed"},
                {"time": "2 hours ago", "order": "Vancomycin 1g IV", "status": "Completed"},
                {"time": "2 hours ago", "order": "Piperacillin-Tazobactam 4.5g IV", "status": "Completed"},
                {"time": "1 hour ago", "order": "Lactate level q4h", "status": "Pending"},
                {"time": "30 min ago", "order": "Fluid bolus 1L NS", "status": "In Progress"}
            ]
        },
        {
            "patient_id": "ICU-2024-002",
            "mrn": "MRN-923847",
            "age": 54,
            "gender": "Female",
            "admission_time": (datetime.now() - timedelta(hours=12)).isoformat(),
            "location": "ICU Bed 08B",
            "vitals": {
                "heart_rate": 105.0, "systolic_bp": 108.0, "diastolic_bp": 68.0,
                "mean_arterial_pressure": 81.0, "respiratory_rate": 22.0,
                "temperature": 38.2, "spo2": 94.0
            },
            "labs": {
                "wbc": 14200.0, "platelet_count": 145000.0, "creatinine": 1.3,
                "bilirubin": 1.1, "lactate": 2.1, "procalcitonin": 3.2, "crp": 98.0
            },
            "sofa_score": {
                "respiration": 1, "coagulation": 0, "liver": 0,
                "cardiovascular": 1, "cns": 0, "renal": 1, "total": 3
            },
            "model_prediction": {
                "sepsis_probability": 0.58, "risk_level": "MODERATE", "confidence": 0.78,
                "feature_importance": {
                    "heart_rate": 0.16, "procalcitonin": 0.14, "wbc": 0.13,
                    "lactate": 0.12, "temperature": 0.11
                }
            },
            "clinical_notes": "54F with UTI symptoms. Fever and flank pain. Urine culture pending. Responsive to fluids.",
            "orders": [
                {"time": "6 hours ago", "order": "Urine culture", "status": "Pending"},
                {"time": "6 hours ago", "order": "Ceftriaxone 1g IV", "status": "Completed"},
                {"time": "4 hours ago", "order": "Fluid bolus 500ml", "status": "Completed"}
            ]
        },
        {
            "patient_id": "ICU-2024-003",
            "mrn": "MRN-741852",
            "age": 72,
            "gender": "Male",
            "admission_time": (datetime.now() - timedelta(hours=18)).isoformat(),
            "location": "ICU Bed 15C",
            "vitals": {
                "heart_rate": 135.0, "systolic_bp": 78.0, "diastolic_bp": 45.0,
                "mean_arterial_pressure": 56.0, "respiratory_rate": 32.0,
                "temperature": 39.5, "spo2": 87.0
            },
            "labs": {
                "wbc": 24800.0, "platelet_count": 62000.0, "creatinine": 3.8,
                "bilirubin": 3.2, "lactate": 5.8, "procalcitonin": 18.7, "crp": 285.0
            },
            "sofa_score": {
                "respiration": 3, "coagulation": 2, "liver": 2,
                "cardiovascular": 3, "cns": 1, "renal": 3, "total": 14
            },
            "model_prediction": {
                "sepsis_probability": 0.96, "risk_level": "CRITICAL", "confidence": 0.97,
                "feature_importance": {
                    "lactate": 0.22, "sofa_total": 0.19, "map": 0.16,
                    "procalcitonin": 0.14, "platelet_count": 0.12
                }
            },
            "clinical_notes": "72M in septic shock. On norepinephrine 0.15mcg/kg/min. Suspected intra-abdominal source. CT shows possible bowel perforation. Surgery consulted.",
            "orders": [
                {"time": "12 hours ago", "order": "Norepinephrine gtt", "status": "Active"},
                {"time": "10 hours ago", "order": "CT abdomen/pelvis", "status": "Completed"},
                {"time": "8 hours ago", "order": "Surgical consult", "status": "Completed"},
                {"time": "2 hours ago", "order": "Vasopressin gtt", "status": "Active"}
            ]
        }
    ]


# 
#  CHART BUILDERS (Dark Theme)
# 
CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(15,23,42,0.0)",
    plot_bgcolor="rgba(15,23,42,0.6)",
    font=dict(family="Inter", color="#94a3b8"),
    margin=dict(l=40, r=20, t=50, b=40),
)


def create_risk_gauge(probability: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability * 100,
        number=dict(suffix="%", font=dict(size=42, color="#f1f5f9")),
        title=dict(text="Sepsis Probability", font=dict(size=14, color="#64748b")),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="#334155", dtick=20),
            bar=dict(color="#38bdf8", thickness=0.3),
            bgcolor="rgba(15,23,42,0.6)",
            borderwidth=0,
            steps=[
                dict(range=[0, 30], color="rgba(34,197,94,0.2)"),
                dict(range=[30, 60], color="rgba(245,158,11,0.2)"),
                dict(range=[60, 80], color="rgba(249,115,22,0.2)"),
                dict(range=[80, 100], color="rgba(239,68,68,0.2)")
            ],
            threshold=dict(line=dict(color="#ef4444", width=3), thickness=0.8, value=80)
        )
    ))
    fig.update_layout(**CHART_LAYOUT, height=280)
    return fig


def create_feature_importance_chart(features: Dict) -> go.Figure:
    df = pd.DataFrame(list(features.items()), columns=['Feature', 'Importance'])
    df = df.sort_values('Importance', ascending=True)
    colors = ['#38bdf8' if v < 0.15 else '#f59e0b' if v < 0.18 else '#ef4444' for v in df['Importance']]

    fig = go.Figure(go.Bar(
        y=df['Feature'], x=df['Importance'], orientation='h',
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{x:.0%}" for x in df['Importance']], textposition='outside',
        textfont=dict(color="#94a3b8", size=11)
    ))
    fig.update_layout(
        **CHART_LAYOUT, height=280,
        title=dict(text="Feature Importance", font=dict(size=14, color="#64748b")),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False)
    )
    return fig


# 
#  VITAL SIGN HELPERS
# 
VITAL_RANGES = {
    'heart_rate': (60, 100), 'systolic_bp': (90, 120), 'diastolic_bp': (60, 80),
    'mean_arterial_pressure': (65, 110), 'respiratory_rate': (12, 20),
    'temperature': (36.5, 37.5), 'spo2': (95, 100)
}
VITAL_LABELS = {
    'heart_rate': ('HR', 'bpm'), 'systolic_bp': ('SBP', 'mmHg'),
    'diastolic_bp': ('DBP', 'mmHg'), 'mean_arterial_pressure': ('MAP', 'mmHg'),
    'respiratory_rate': ('RR', '/min'), 'temperature': ('Temp', '°C'),
    'spo2': ('SpO₂', '%')
}


def vital_status(key, val):
    lo, hi = VITAL_RANGES.get(key, (0, 9999))
    if val < lo * 0.85 or val > hi * 1.15:
        return 'vital-danger'
    if val < lo or val > hi:
        return 'vital-warning'
    return 'vital-normal'


def render_vitals(vitals):
    cards = ""
    for key in ['heart_rate', 'systolic_bp', 'diastolic_bp', 'mean_arterial_pressure',
                'respiratory_rate', 'temperature', 'spo2']:
        val = vitals[key]
        label, unit = VITAL_LABELS[key]
        status = vital_status(key, val)
        fmt = f"{val:.1f}" if key == 'temperature' else f"{val:.0f}"
        cards += f"""
        <div class="vital-card {status}">
            <div class="vital-label">{label}</div>
            <div class="vital-value">{fmt}</div>
            <div class="vital-unit">{unit}</div>
        </div>"""
    st.markdown(f'<div class="vital-grid">{cards}</div>', unsafe_allow_html=True)


# 
#  SOFA BREAKDOWN
# 
def render_sofa(sofa):
    parts = ""
    for key in ['respiration', 'coagulation', 'liver', 'cardiovascular', 'cns', 'renal']:
        v = sofa[key]
        parts += f"""
        <div class="sofa-item">
            <div class="sofa-label">{key.title()}</div>
            <div class="sofa-score sofa-{v}">{v}</div>
            <div class="sofa-max">/ 4</div>
        </div>"""
    st.markdown(f'<div class="sofa-grid">{parts}</div>', unsafe_allow_html=True)


# 
#  LAB RESULTS
# 
LAB_CONFIG = [
    ('wbc',            'WBC',           'cells/μL',  4000,   11000,  '4,000–11,000'),
    ('platelet_count', 'Platelets',     '×10³/μL',   150000, 400000, '150,000–400,000'),
    ('creatinine',     'Creatinine',    'mg/dL',     0.6,    1.2,    '0.6–1.2'),
    ('bilirubin',      'Bilirubin',     'mg/dL',     0.1,    1.2,    '0.1–1.2'),
    ('lactate',        'Lactate',       'mmol/L',    0,      2.0,    '<2.0'),
    ('procalcitonin',  'Procalcitonin', 'ng/mL',     0,      0.5,    '<0.5'),
    ('crp',            'CRP',           'mg/L',      0,      10,     '<10'),
]

def render_labs(labs):
    rows = ""
    for key, name, unit, lo, hi, ref in LAB_CONFIG:
        val = labs[key]
        is_abnormal = val < lo or val > hi
        flag = "H" if val > hi else ("L" if val < lo else "")
        flag_cls = "flag-high" if val > hi else ("flag-low" if val < lo else "flag-ok")
        row_cls = "lab-abnormal" if is_abnormal else ""

        if key in ('wbc', 'platelet_count'):
            fmt = f"{val:,.0f}"
        elif key == 'crp':
            fmt = f"{val:.0f}"
        else:
            fmt = f"{val:.1f}"

        rows += f"""
        <div class="lab-row {row_cls}">
            <span class="lab-name">{name}</span>
            <span class="lab-val">{fmt}</span>
            <span class="lab-unit">{unit}</span>
            <span class="lab-ref">{ref}</span>
            <span class="lab-flag {flag_cls}">{flag}</span>
        </div>"""
    st.markdown(f'<div class="panel">{rows}</div>', unsafe_allow_html=True)


# 
#  TIMELINE
# 
def render_timeline(orders):
    entries = ""
    for o in orders:
        dot_cls = {
            'Completed': 'dot-completed', 'Active': 'dot-active',
            'In Progress': 'dot-inprogress', 'Pending': 'dot-pending'
        }.get(o['status'], 'dot-pending')

        status_color = {
            'Completed': '#22c55e', 'Active': '#3b82f6',
            'In Progress': '#f59e0b', 'Pending': '#64748b'
        }.get(o['status'], '#64748b')

        entries += f"""
        <div class="timeline-entry">
            <div class="timeline-dot {dot_cls}"></div>
            <div class="timeline-content">
                <div class="tl-order">{o['order']}</div>
                <div class="tl-meta">{o['time']} · <span style="color:{status_color}">{o['status']}</span></div>
            </div>
        </div>"""
    st.markdown(f'<div class="panel">{entries}</div>', unsafe_allow_html=True)


# 
#  API CALLS
# 
def analyze_patient(patient_data):
    try:
        with st.spinner(' Running AI analysis with clinical guidelines...'):
            r = requests.post(f"{API_URL}/analyze_patient", json={"patient_context": patient_data}, timeout=60)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        return None


def send_chat_message(patient_data, question, history):
    try:
        r = requests.post(f"{API_URL}/chat", json={
            "patient_context": patient_data, "question": question, "chat_history": history
        }, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Chat failed: {str(e)}")
        return None


def check_backend_health():
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        return (True, r.json()) if r.status_code == 200 else (False, None)
    except:
        return (False, None)


# 
#  MAIN APPLICATION
# 
def main():
    apply_custom_css()
    init_session_state()

    #  Sidebar 
    with st.sidebar:
        st.markdown("###  Command Center")
        st.markdown("---")

        is_healthy, health_data = check_backend_health()
        if is_healthy:
            doc_count = health_data.get('documents_loaded', 0) if health_data else 0
            st.markdown(f"""
            <div class="sidebar-stat">
                <div class="stat-label">System Status</div>
                <div class="stat-value" style="color: #22c55e;">  ONLINE</div>
            </div>
            <div class="sidebar-stat">
                <div class="stat-label">Guidelines Indexed</div>
                <div class="stat-value" style="color: #38bdf8;">{doc_count}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error(" Backend Offline")
            st.stop()

        st.markdown("---")
        st.markdown("##### Patient Selection")

        demo_patients = get_demo_patients()
        patient_options = {p['patient_id']: p for p in demo_patients}

        risk_icons = {'HIGH': '', 'MODERATE': '', 'CRITICAL': '', 'LOW': ''}
        selected_id = st.selectbox(
            "Select Patient",
            options=list(patient_options.keys()),
            format_func=lambda x: f"{risk_icons.get(patient_options[x]['model_prediction']['risk_level'], '')} {x} — {patient_options[x]['age']}yo {patient_options[x]['gender'][0]}"
        )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("  Load", use_container_width=True):
                st.session_state.current_patient = patient_options[selected_id]
                st.session_state.analysis_result = None
                st.session_state.chat_history = []
                st.rerun()
        with col_b:
            if st.button("  Clear", use_container_width=True):
                st.session_state.current_patient = None
                st.session_state.analysis_result = None
                st.session_state.chat_history = []
                st.rerun()

        if st.session_state.current_patient:
            p = st.session_state.current_patient
            st.markdown("---")
            st.markdown("##### Quick Indicators")
            sofa_color = '#22c55e' if p['sofa_score']['total'] < 6 else '#f59e0b' if p['sofa_score']['total'] < 10 else '#ef4444'
            lac_color  = '#22c55e' if p['labs']['lactate'] < 2 else '#f59e0b' if p['labs']['lactate'] < 4 else '#ef4444'
            map_color  = '#22c55e' if p['vitals']['mean_arterial_pressure'] >= 65 else '#ef4444'
            st.markdown(f"""
            <div class="sidebar-stat"><div class="stat-label">SOFA Score</div><div class="stat-value" style="color:{sofa_color};">{p['sofa_score']['total']}<span style="font-size:14px;color:#475569;">/24</span></div></div>
            <div class="sidebar-stat"><div class="stat-label">Lactate</div><div class="stat-value" style="color:{lac_color};">{p['labs']['lactate']}<span style="font-size:14px;color:#475569;"> mmol/L</span></div></div>
            <div class="sidebar-stat"><div class="stat-label">MAP</div><div class="stat-value" style="color:{map_color};">{p['vitals']['mean_arterial_pressure']:.0f}<span style="font-size:14px;color:#475569;"> mmHg</span></div></div>
            """, unsafe_allow_html=True)

    #  System Bar 
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

    #  Welcome Screen (no patient) 
    if not st.session_state.current_patient:
        st.markdown("""
        <div class="welcome-screen">
            <div class="welcome-icon"></div>
            <h1>Sepsis Clinical Decision Support</h1>
            <p>AI-powered clinical analysis with evidence-based guideline retrieval</p>
            <div class="welcome-features">
                <div class="feature-box">
                    <div class="feat-icon"></div>
                    <div class="feat-title">Real-Time Monitoring</div>
                    <div class="feat-desc">Vitals, labs & SOFA scoring</div>
                </div>
                <div class="feature-box">
                    <div class="feat-icon"></div>
                    <div class="feat-title">AI Analysis</div>
                    <div class="feat-desc">RAG-powered clinical reasoning</div>
                </div>
                <div class="feature-box">
                    <div class="feat-icon"></div>
                    <div class="feat-title">Clinical Chat</div>
                    <div class="feat-desc">Evidence-based Q&A assistant</div>
                </div>
                <div class="feature-box">
                    <div class="feat-icon"></div>
                    <div class="feat-title">Order Tracking</div>
                    <div class="feat-desc">Clinical timeline & history</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    patient = st.session_state.current_patient

    #  Patient Banner 
    risk = patient['model_prediction']['risk_level']
    risk_cls = f"risk-{risk.lower()}"
    avatar_bg = {'CRITICAL': '#dc2626', 'HIGH': '#ea580c', 'MODERATE': '#d97706', 'LOW': '#16a34a'}.get(risk, '#64748b')
    initials = f"{patient['gender'][0]}{patient['age']}"
    adm = datetime.fromisoformat(patient['admission_time'])
    los_hours = int((datetime.now() - adm).total_seconds() / 3600)

    st.markdown(f"""
    <div class="patient-banner">
        <div class="pt-info">
            <div class="pt-avatar" style="background:{avatar_bg};">{initials}</div>
            <div class="pt-details">
                <h2>{patient['patient_id']}</h2>
                <div class="pt-meta">
                    <span> {patient.get('location', 'ICU')}</span>
                    <span> {patient.get('mrn', 'N/A')}</span>
                    <span> LOS: {los_hours}h</span>
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "  Monitoring", "  AI Analysis", "  Clinical Chat", "  Laboratory", "  Orders"
    ])

    #  TAB 1: Monitoring 
    with tab1:
        st.markdown('<div class="panel-header"> Vital Signs</div>', unsafe_allow_html=True)
        render_vitals(patient['vitals'])

        st.markdown("")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="panel-header"> Sepsis Risk Assessment</div>', unsafe_allow_html=True)
            st.plotly_chart(create_risk_gauge(patient['model_prediction']['sepsis_probability']), use_container_width=True)
        with col2:
            st.markdown('<div class="panel-header"> Model Feature Importance</div>', unsafe_allow_html=True)
            st.plotly_chart(create_feature_importance_chart(patient['model_prediction']['feature_importance']), use_container_width=True)

        st.markdown("")
        col3, col4 = st.columns([1, 1])
        with col3:
            st.markdown(f'<div class="panel-header"> SOFA Score — Total: {patient["sofa_score"]["total"]}/24</div>', unsafe_allow_html=True)
            render_sofa(patient['sofa_score'])
        with col4:
            st.markdown('<div class="panel-header"> Clinical Notes</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="clinical-note">{patient.get("clinical_notes", "No notes available")}</div>', unsafe_allow_html=True)

    #  TAB 2: AI Analysis 
    with tab2:
        col_btn1, col_btn2, _ = st.columns([1, 1, 4])
        with col_btn1:
            if st.button("  Generate Analysis", type="primary", use_container_width=True):
                result = analyze_patient(patient)
                if result:
                    st.session_state.analysis_result = result
        with col_btn2:
            if st.button("  Clear", use_container_width=True):
                st.session_state.analysis_result = None

        if st.session_state.analysis_result:
            analysis = st.session_state.analysis_result
            urgency = analysis.get('urgency_level', 'MODERATE')
            alert_cls = {'CRITICAL': 'alert-critical', 'HIGH': 'alert-high'}.get(urgency, 'alert-moderate')
            urgency_icon = {'CRITICAL': '', 'HIGH': ''}.get(urgency, 'ℹ')

            st.markdown(f'<div class="{alert_cls}">{urgency_icon} URGENCY LEVEL: {urgency}</div>', unsafe_allow_html=True)

            col_f, col_r = st.columns(2)
            with col_f:
                st.markdown('<div class="panel-header"> Key Findings</div>', unsafe_allow_html=True)
                for f in analysis.get('key_findings', []):
                    st.markdown(f'<div class="finding-card"> {f}</div>', unsafe_allow_html=True)
            with col_r:
                st.markdown('<div class="panel-header"> Risk Factors</div>', unsafe_allow_html=True)
                for r in analysis.get('risk_factors', []):
                    st.markdown(f'<div class="risk-card"> {r}</div>', unsafe_allow_html=True)

            st.markdown('<div class="panel-header"> Evidence-Based Recommendations</div>', unsafe_allow_html=True)
            for i, rec in enumerate(analysis.get('recommendations', []), 1):
                st.markdown(f'<div class="rec-card"><strong>{i}.</strong> {rec}</div>', unsafe_allow_html=True)

            with st.expander(" View Full Clinical Reasoning Chain"):
                st.markdown(f'<div class="clinical-note">{analysis.get("reasoning", "No reasoning available")}</div>', unsafe_allow_html=True)

    #  TAB 3: Clinical Chat 
    with tab3:
        st.markdown('<div class="panel-header"> Clinical Decision Support Chat</div>', unsafe_allow_html=True)

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("Ask about this patient's clinical presentation..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            with st.chat_message("assistant"):
                with st.spinner(" Searching clinical guidelines..."):
                    response = send_chat_message(patient, prompt, st.session_state.chat_history[:-1])
                if response:
                    st.write(response["answer"])
                    with st.expander(" Retrieved Clinical Guidelines"):
                        for i, doc in enumerate(response.get("retrieved_documents", []), 1):
                            st.markdown(f"**Source {i}: {doc['source']}** (Relevance: {doc['relevance_score']:.2f})")
                            st.text(doc['content'][:400] + "...")
                            st.markdown("---")
                    with st.expander(" Reasoning Steps"):
                        for i, step in enumerate(response.get("reasoning_chain", []), 1):
                            st.markdown(f"{i}. {step}")
                    st.session_state.chat_history.append({"role": "assistant", "content": response["answer"]})

    #  TAB 4: Laboratory 
    with tab4:
        st.markdown('<div class="panel-header"> Complete Laboratory Panel</div>', unsafe_allow_html=True)
        render_labs(patient['labs'])

    #  TAB 5: Orders 
    with tab5:
        st.markdown('<div class="panel-header"> Clinical Orders & Timeline</div>', unsafe_allow_html=True)
        if 'orders' in patient and patient['orders']:
            render_timeline(patient['orders'])
        else:
            st.info("No orders recorded for this patient")


if __name__ == "__main__":
    main()
