"""
COPY-PASTE CODE SNIPPETS FOR YOUR JUPYTER NOTEBOOK
===================================================

Add these code cells to your sepsis prediction notebook to export 
MIMIC patients to the RAG system.
"""

# ============================================================================
# SNIPPET 1: SETUP (Add at the beginning of your notebook)
# ============================================================================

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add path to RAG scripts
sys.path.append('../sepsis_rag_v2/scripts')
from mimic_integration import MIMICToRAGConverter

# Initialize converter
converter = MIMICToRAGConverter(output_dir='../sepsis_rag_v2/data/mimic_patients')

print(" MIMIC-to-RAG converter initialized")


# ============================================================================
# SNIPPET 2: EXPORT SINGLE PATIENT (Add after your model runs)
# ============================================================================

# After you have predictions for a patient, use this to export:

def export_patient_to_rag(subject_id, vitals_df, labs_df, sofa_dict, 
                          prediction_dict, demographics_dict):
    """
    Export a single patient to RAG system.
    
    Args:
        subject_id: MIMIC subject_id or hadm_id
        vitals_df: DataFrame with columns [heart_rate, sbp, dbp, map, resp_rate, temperature, spo2]
        labs_df: DataFrame with columns [wbc, platelet, creatinine, bilirubin, lactate, procalcitonin, crp]
        sofa_dict: {'respiration': 2, 'coagulation': 1, 'liver': 0, 'cardiovascular': 2, 'cns': 0, 'renal': 1}
        prediction_dict: {'probability': 0.87, 'risk_level': 'HIGH', 'confidence': 0.92, 'feature_importance': {...}}
        demographics_dict: {'age': 67, 'gender': 'M'}
    """
    
    patient_data = converter.convert_patient(
        patient_id=f"MIMIC-{subject_id}",
        vitals_df=vitals_df,
        labs_df=labs_df,
        sofa_components=sofa_dict,
        model_prediction=prediction_dict,
        demographics=demographics_dict,
        clinical_notes=f"MIMIC patient {subject_id}"
    )
    
    filepath = converter.save_patient(patient_data)
    return filepath

# Example usage:
# export_patient_to_rag(
#     subject_id=12345,
#     vitals_df=patient_vitals,
#     labs_df=patient_labs,
#     sofa_dict=sofa_scores,
#     prediction_dict={'probability': y_pred_proba, 'risk_level': risk_tier, ...},
#     demographics_dict={'age': age, 'gender': gender}
# )


# ============================================================================
# SNIPPET 3: QUICK EXPORT FROM VARIABLES (If data is in memory)
# ============================================================================

# If you have individual variables instead of DataFrames:

def quick_export(subject_id, 
                 # Vitals
                 hr, sbp, dbp, map_val, rr, temp, spo2,
                 # Labs
                 wbc, platelet, creat, bili, lactate, pct=None, crp=None,
                 # SOFA
                 sofa_resp, sofa_coag, sofa_liver, sofa_cardio, sofa_cns, sofa_renal,
                 # Prediction
                 sepsis_prob, risk_level, confidence, feature_importance,
                 # Demographics
                 age, gender):
    
    # Create DataFrames
    vitals_df = pd.DataFrame({
        'heart_rate': [hr],
        'sbp': [sbp],
        'dbp': [dbp],
        'map': [map_val],
        'resp_rate': [rr],
        'temperature': [temp],
        'spo2': [spo2]
    })
    
    labs_df = pd.DataFrame({
        'wbc': [wbc],
        'platelet': [platelet],
        'creatinine': [creat],
        'bilirubin': [bili],
        'lactate': [lactate],
        'procalcitonin': [pct],
        'crp': [crp]
    })
    
    sofa_dict = {
        'respiration': int(sofa_resp),
        'coagulation': int(sofa_coag),
        'liver': int(sofa_liver),
        'cardiovascular': int(sofa_cardio),
        'cns': int(sofa_cns),
        'renal': int(sofa_renal)
    }
    
    prediction_dict = {
        'probability': float(sepsis_prob),
        'risk_level': str(risk_level),
        'confidence': float(confidence),
        'feature_importance': feature_importance
    }
    
    demographics_dict = {
        'age': int(age),
        'gender': str(gender)
    }
    
    patient_data = converter.convert_patient(
        patient_id=f"MIMIC-{subject_id}",
        vitals_df=vitals_df,
        labs_df=labs_df,
        sofa_components=sofa_dict,
        model_prediction=prediction_dict,
        demographics=demographics_dict
    )
    
    filepath = converter.save_patient(patient_data)
    print(f" Exported patient MIMIC-{subject_id} to {filepath}")
    return filepath

# Example usage:
# quick_export(
#     subject_id=12345,
#     hr=118, sbp=92, dbp=58, map_val=69, rr=28, temp=38.8, spo2=91,
#     wbc=18500, platelet=95000, creat=2.4, bili=1.8, lactate=3.2, pct=8.5, crp=185,
#     sofa_resp=2, sofa_coag=1, sofa_liver=1, sofa_cardio=2, sofa_cns=0, sofa_renal=2,
#     sepsis_prob=0.87, risk_level='HIGH', confidence=0.92, feature_importance=feat_imp,
#     age=67, gender='M'
# )


# ============================================================================
# SNIPPET 4: BATCH EXPORT (Export multiple patients at once)
# ============================================================================

def batch_export_top_patients(predictions_df, vitals_df, labs_df, sofa_df, 
                               demographics_df, n_patients=10, 
                               patient_id_col='subject_id'):
    """
    Export top N high-risk patients to RAG system.
    
    Args:
        predictions_df: DataFrame with [subject_id, sepsis_probability, risk_level, confidence]
        vitals_df: DataFrame with [subject_id, heart_rate, sbp, dbp, map, resp_rate, temperature, spo2]
        labs_df: DataFrame with [subject_id, wbc, platelet, creatinine, bilirubin, lactate, ...]
        sofa_df: DataFrame with [subject_id, sofa_respiration, sofa_coagulation, ...]
        demographics_df: DataFrame with [subject_id, age, gender]
        n_patients: Number of patients to export
    """
    
    # Get high-risk patients
    high_risk = predictions_df.nlargest(n_patients, 'sepsis_probability')
    
    exported = []
    
    for idx, pred_row in high_risk.iterrows():
        subject_id = pred_row[patient_id_col]
        
        try:
            # Get patient data
            p_vitals = vitals_df[vitals_df[patient_id_col] == subject_id]
            p_labs = labs_df[labs_df[patient_id_col] == subject_id]
            p_sofa = sofa_df[sofa_df[patient_id_col] == subject_id].iloc[0]
            p_demo = demographics_df[demographics_df[patient_id_col] == subject_id].iloc[0]
            
            # Convert
            patient_data = converter.convert_patient(
                patient_id=f"MIMIC-{subject_id}",
                vitals_df=p_vitals,
                labs_df=p_labs,
                sofa_components={
                    'respiration': int(p_sofa.get('sofa_respiration', 0)),
                    'coagulation': int(p_sofa.get('sofa_coagulation', 0)),
                    'liver': int(p_sofa.get('sofa_liver', 0)),
                    'cardiovascular': int(p_sofa.get('sofa_cardiovascular', 0)),
                    'cns': int(p_sofa.get('sofa_cns', 0)),
                    'renal': int(p_sofa.get('sofa_renal', 0))
                },
                model_prediction={
                    'probability': float(pred_row['sepsis_probability']),
                    'risk_level': str(pred_row['risk_level']),
                    'confidence': float(pred_row.get('confidence', 0.7)),
                    'feature_importance': eval(pred_row.get('feature_importance', '{}'))
                },
                demographics={
                    'age': int(p_demo['age']),
                    'gender': str(p_demo['gender'])
                }
            )
            
            filepath = converter.save_patient(patient_data)
            exported.append(subject_id)
            
        except Exception as e:
            print(f" Failed to export patient {subject_id}: {e}")
            continue
    
    print(f"\n Successfully exported {len(exported)} patients")
    return exported

# Example usage:
# batch_export_top_patients(
#     predictions_df=predictions_df,
#     vitals_df=vitals_final_df,
#     labs_df=labs_final_df,
#     sofa_df=sofa_scores_df,
#     demographics_df=patients_df,
#     n_patients=10
# )


# ============================================================================
# SNIPPET 5: VERIFY EXPORT
# ============================================================================

import json

def verify_exported_patient(subject_id):
    """Check if patient was exported correctly."""
    
    filepath = Path(f'../sepsis_rag_v2/data/mimic_patients/MIMIC-{subject_id}.json')
    
    if not filepath.exists():
        print(f" Patient MIMIC-{subject_id} not found")
        return None
    
    with open(filepath, 'r') as f:
        patient = json.load(f)
    
    print(f" Patient MIMIC-{subject_id} exported successfully")
    print(f"   Age: {patient['age']}")
    print(f"   Gender: {patient['gender']}")
    print(f"   Risk Level: {patient['model_prediction']['risk_level']}")
    print(f"   Sepsis Probability: {patient['model_prediction']['sepsis_probability']:.1%}")
    print(f"   SOFA Total: {patient['sofa_score']['total']}")
    print(f"   Heart Rate: {patient['vitals']['heart_rate']} bpm")
    print(f"   Lactate: {patient['labs']['lactate']} mmol/L")
    
    return patient

# Example usage:
# verify_exported_patient(12345)


# ============================================================================
# SNIPPET 6: LIST ALL EXPORTED PATIENTS
# ============================================================================

import os

def list_exported_patients():
    """List all patients that have been exported."""
    
    export_dir = Path('../sepsis_rag_v2/data/mimic_patients')
    export_dir.mkdir(parents=True, exist_ok=True)
    
    patient_files = list(export_dir.glob('MIMIC-*.json'))
    
    if not patient_files:
        print("No patients exported yet")
        return []
    
    print(f"Found {len(patient_files)} exported patients:\n")
    
    patients_info = []
    
    for filepath in sorted(patient_files):
        with open(filepath, 'r') as f:
            patient = json.load(f)
        
        info = {
            'patient_id': patient['patient_id'],
            'risk_level': patient['model_prediction']['risk_level'],
            'sepsis_prob': patient['model_prediction']['sepsis_probability'],
            'sofa_total': patient['sofa_score']['total']
        }
        patients_info.append(info)
        
        print(f"{info['patient_id']}: {info['risk_level']} risk "
              f"({info['sepsis_prob']:.1%} probability, SOFA {info['sofa_total']})")
    
    return patients_info

# Example usage:
# list_exported_patients()


# ============================================================================
# SNIPPET 7: COMPLETE WORKFLOW EXAMPLE
# ============================================================================

def complete_export_workflow_example():
    """
    Complete example showing the full workflow.
    Adapt this to your specific notebook structure.
    """
    
    print("=" * 60)
    print("MIMIC to RAG Export Workflow")
    print("=" * 60)
    
    # Example: Get a high-risk patient from your predictions
    high_risk_patients = predictions_df[predictions_df['risk_level'] == 'HIGH']
    
    if len(high_risk_patients) == 0:
        print("No high-risk patients found")
        return
    
    # Take the first high-risk patient
    patient_row = high_risk_patients.iloc[0]
    subject_id = patient_row['subject_id']
    
    print(f"\n1⃣ Selected patient: MIMIC-{subject_id}")
    print(f"   Sepsis probability: {patient_row['sepsis_probability']:.1%}")
    print(f"   Risk level: {patient_row['risk_level']}")
    
    # Get patient vitals (from your data)
    patient_vitals = vitals_df[vitals_df['subject_id'] == subject_id]
    print(f"\n2⃣ Retrieved {len(patient_vitals)} vital sign records")
    
    # Get patient labs (from your data)
    patient_labs = labs_df[labs_df['subject_id'] == subject_id]
    print(f"3⃣ Retrieved {len(patient_labs)} lab results")
    
    # Get SOFA scores (from your data)
    patient_sofa = sofa_df[sofa_df['subject_id'] == subject_id].iloc[0]
    sofa_total = sum([
        patient_sofa.get('sofa_respiration', 0),
        patient_sofa.get('sofa_coagulation', 0),
        patient_sofa.get('sofa_liver', 0),
        patient_sofa.get('sofa_cardiovascular', 0),
        patient_sofa.get('sofa_cns', 0),
        patient_sofa.get('sofa_renal', 0)
    ])
    print(f"4⃣ SOFA score: {sofa_total}/24")
    
    # Export to RAG
    print(f"\n5⃣ Exporting to RAG system...")
    
    filepath = export_patient_to_rag(
        subject_id=subject_id,
        vitals_df=patient_vitals,
        labs_df=patient_labs,
        sofa_dict={
            'respiration': int(patient_sofa.get('sofa_respiration', 0)),
            'coagulation': int(patient_sofa.get('sofa_coagulation', 0)),
            'liver': int(patient_sofa.get('sofa_liver', 0)),
            'cardiovascular': int(patient_sofa.get('sofa_cardiovascular', 0)),
            'cns': int(patient_sofa.get('sofa_cns', 0)),
            'renal': int(patient_sofa.get('sofa_renal', 0))
        },
        prediction_dict={
            'probability': float(patient_row['sepsis_probability']),
            'risk_level': str(patient_row['risk_level']),
            'confidence': float(patient_row.get('confidence', 0.8)),
            'feature_importance': {}  # Add your feature importance here
        },
        demographics_dict={
            'age': int(patients_df[patients_df['subject_id'] == subject_id].iloc[0]['age']),
            'gender': str(patients_df[patients_df['subject_id'] == subject_id].iloc[0]['gender'])
        }
    )
    
    print(f"\n Export complete!")
    print(f"   File saved to: {filepath}")
    print(f"\n6⃣ Next steps:")
    print(f"   • cd sepsis_rag_v2")
    print(f"   • ./start.sh")
    print(f"   • Open http://localhost:8501")
    print(f"   • Load patient MIMIC-{subject_id}")
    
# Run the example:
# complete_export_workflow_example()


# ============================================================================
# USAGE INSTRUCTIONS
# ============================================================================

"""
HOW TO USE THESE SNIPPETS:

1. Add SNIPPET 1 at the beginning of your notebook (after imports)

2. After you run your sepsis prediction model, choose ONE of:
   - SNIPPET 2: If you have organized DataFrames
   - SNIPPET 3: If you have individual variables
   - SNIPPET 4: To export multiple patients at once

3. Use SNIPPET 5 to verify the export worked

4. Use SNIPPET 6 to see all exported patients

5. Then run the RAG system:
   cd sepsis_rag_v2
   ./start.sh

Your MIMIC patients will now appear in the RAG interface!

========================================================================
MINIMAL EXAMPLE (Copy this entire block):
========================================================================

import sys
sys.path.append('../sepsis_rag_v2/scripts')
from mimic_integration import MIMICToRAGConverter
import pandas as pd

converter = MIMICToRAGConverter(output_dir='../sepsis_rag_v2/data/mimic_patients')

# Prepare your data
vitals_df = pd.DataFrame({
    'heart_rate': [118], 'sbp': [92], 'dbp': [58], 'map': [69],
    'resp_rate': [28], 'temperature': [38.8], 'spo2': [91]
})

labs_df = pd.DataFrame({
    'wbc': [18500], 'platelet': [95000], 'creatinine': [2.4],
    'bilirubin': [1.8], 'lactate': [3.2], 'procalcitonin': [8.5], 'crp': [185]
})

# Convert and save
patient_data = converter.convert_patient(
    patient_id="MIMIC-12345",
    vitals_df=vitals_df,
    labs_df=labs_df,
    sofa_components={'respiration': 2, 'coagulation': 1, 'liver': 1, 
                     'cardiovascular': 2, 'cns': 0, 'renal': 2},
    model_prediction={'probability': 0.87, 'risk_level': 'HIGH', 
                     'confidence': 0.92, 'feature_importance': {}},
    demographics={'age': 67, 'gender': 'M'}
)

converter.save_patient(patient_data)
print(" Patient exported! Now run: cd sepsis_rag_v2 && ./start.sh")

========================================================================
"""
