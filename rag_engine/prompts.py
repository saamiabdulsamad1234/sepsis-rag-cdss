from typing import Dict, List
from models.schemas import PatientContext

class PromptTemplates:
    
    @staticmethod
    def create_patient_summary(patient: PatientContext) -> str:
        summary = f"""
PATIENT CLINICAL SUMMARY
========================
Patient ID: {patient.patient_id}
Demographics: {patient.age} years old, {patient.gender}

VITAL SIGNS:
- Heart Rate: {patient.vitals.heart_rate} bpm
- Blood Pressure: {patient.vitals.systolic_bp}/{patient.vitals.diastolic_bp} mmHg
- Mean Arterial Pressure: {patient.vitals.mean_arterial_pressure} mmHg
- Respiratory Rate: {patient.vitals.respiratory_rate} breaths/min
- Temperature: {patient.vitals.temperature}°C
- SpO2: {patient.vitals.spo2}%

LABORATORY RESULTS:
- WBC: {patient.labs.wbc} cells/μL
- Platelet Count: {patient.labs.platelet_count} × 10³/μL
- Creatinine: {patient.labs.creatinine} mg/dL
- Bilirubin: {patient.labs.bilirubin} mg/dL
- Lactate: {patient.labs.lactate} mmol/L
- Procalcitonin: {patient.labs.procalcitonin} ng/mL
- CRP: {patient.labs.crp} mg/L

SOFA SCORE BREAKDOWN:
- Respiration: {patient.sofa_score.respiration}/4
- Coagulation: {patient.sofa_score.coagulation}/4
- Liver: {patient.sofa_score.liver}/4
- Cardiovascular: {patient.sofa_score.cardiovascular}/4
- CNS: {patient.sofa_score.cns}/4
- Renal: {patient.sofa_score.renal}/4
- TOTAL SOFA: {patient.sofa_score.total}/24

MODEL PREDICTION:
- Sepsis Probability: {patient.model_prediction.sepsis_probability:.2%}
- Risk Level: {patient.model_prediction.risk_level.value}
- Confidence: {patient.model_prediction.confidence:.2%}

CLINICAL NOTES:
{patient.clinical_notes or 'No additional notes'}
"""
        return summary.strip()
    
    @staticmethod
    def create_analysis_prompt(patient_summary: str, retrieved_docs: str) -> str:
        return f"""
You are an expert clinical decision support AI specializing in sepsis management. 
Analyze the following patient data and provide a comprehensive clinical assessment.

{patient_summary}

RELEVANT CLINICAL GUIDELINES:
{retrieved_docs}

TASK:
Provide a detailed clinical analysis including:
1. Summary of the patient's current status
2. Key clinical findings that are concerning
3. Identified risk factors for sepsis progression
4. Evidence-based recommendations based on the guidelines
5. Urgency level assessment
6. Step-by-step clinical reasoning

Format your response as a structured clinical assessment. Be specific, cite guideline 
recommendations, and explain your reasoning clearly.
"""
    
    @staticmethod
    def create_chat_prompt(
        patient_summary: str, 
        retrieved_docs: str, 
        question: str,
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        history_text = ""
        if chat_history:
            history_text = "\n\nPREVIOUS CONVERSATION:\n"
            for msg in chat_history[-5:]:
                history_text += f"{msg['role'].upper()}: {msg['content']}\n"
        
        return f"""
You are an expert clinical decision support AI specializing in sepsis management.
Answer the clinician's question based on the patient data and relevant guidelines.

{patient_summary}

RELEVANT CLINICAL GUIDELINES:
{retrieved_docs}
{history_text}

CLINICIAN'S QUESTION:
{question}

INSTRUCTIONS:
1. Provide a clear, evidence-based answer
2. Reference specific guidelines when applicable
3. Explain your clinical reasoning step-by-step
4. Highlight any critical findings or recommendations
5. Be precise and actionable

Respond in a professional, clinical manner. If the question cannot be answered with 
the available information, clearly state what additional data would be needed.
"""
    
    @staticmethod
    def create_reasoning_extraction_prompt(response: str) -> str:
        return f"""
Extract the key reasoning steps from the following clinical analysis.
List them as a numbered sequence of logical steps.

ANALYSIS:
{response}

Provide ONLY the reasoning chain as a JSON array of strings, like:
["Step 1: ...", "Step 2: ...", "Step 3: ..."]
"""
    
    @staticmethod
    def create_citation_extraction_prompt(response: str, retrieved_docs: str) -> str:
        return f"""
Extract citations from the clinical analysis based on the source documents.

ANALYSIS:
{response}

SOURCE DOCUMENTS:
{retrieved_docs}

Provide ONLY a JSON array of citation strings that reference specific guidelines or 
evidence mentioned in the analysis, like:
["Surviving Sepsis Campaign Guidelines 2021", "SOFA Score Criteria"]
"""
    
    @staticmethod
    def format_retrieved_docs(documents: List) -> str:
        formatted = ""
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('source', 'Unknown')
            formatted += f"\n[Source {i}: {source}]\n{doc.page_content}\n"
            formatted += "-" * 80 + "\n"
        return formatted
