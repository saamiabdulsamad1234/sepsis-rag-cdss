import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

def create_test_patients():
    patients = [
        {
            "patient_id": "PT-HIGH-001",
            "age": 67,
            "gender": "Male",
            "admission_time": datetime.now().isoformat(),
            "vitals": {
                "heart_rate": 118.0,
                "systolic_bp": 92.0,
                "diastolic_bp": 58.0,
                "mean_arterial_pressure": 69.0,
                "respiratory_rate": 28.0,
                "temperature": 38.8,
                "spo2": 91.0
            },
            "labs": {
                "wbc": 18500.0,
                "platelet_count": 95000.0,
                "creatinine": 2.4,
                "bilirubin": 1.8,
                "lactate": 3.2,
                "procalcitonin": 8.5,
                "crp": 185.0
            },
            "sofa_score": {
                "respiration": 2,
                "coagulation": 1,
                "liver": 1,
                "cardiovascular": 2,
                "cns": 0,
                "renal": 2,
                "total": 8
            },
            "model_prediction": {
                "sepsis_probability": 0.87,
                "risk_level": "HIGH",
                "confidence": 0.92,
                "feature_importance": {
                    "lactate": 0.18,
                    "heart_rate": 0.15,
                    "sofa_total": 0.14,
                    "procalcitonin": 0.12,
                    "map": 0.11
                }
            },
            "clinical_notes": "67-year-old male admitted from ED with suspected pneumonia. Increasing oxygen requirements. Chest X-ray shows bilateral infiltrates."
        },
        {
            "patient_id": "PT-MODERATE-002",
            "age": 54,
            "gender": "Female",
            "admission_time": datetime.now().isoformat(),
            "vitals": {
                "heart_rate": 105.0,
                "systolic_bp": 108.0,
                "diastolic_bp": 68.0,
                "mean_arterial_pressure": 81.0,
                "respiratory_rate": 22.0,
                "temperature": 38.2,
                "spo2": 94.0
            },
            "labs": {
                "wbc": 14200.0,
                "platelet_count": 145000.0,
                "creatinine": 1.3,
                "bilirubin": 1.1,
                "lactate": 2.1,
                "procalcitonin": 3.2,
                "crp": 98.0
            },
            "sofa_score": {
                "respiration": 1,
                "coagulation": 0,
                "liver": 0,
                "cardiovascular": 1,
                "cns": 0,
                "renal": 1,
                "total": 3
            },
            "model_prediction": {
                "sepsis_probability": 0.58,
                "risk_level": "MODERATE",
                "confidence": 0.78,
                "feature_importance": {
                    "heart_rate": 0.16,
                    "procalcitonin": 0.14,
                    "wbc": 0.13,
                    "lactate": 0.12,
                    "temperature": 0.11
                }
            },
            "clinical_notes": "54-year-old female with UTI symptoms. Fever and flank pain. Urine culture pending."
        },
        {
            "patient_id": "PT-CRITICAL-003",
            "age": 72,
            "gender": "Male",
            "admission_time": datetime.now().isoformat(),
            "vitals": {
                "heart_rate": 135.0,
                "systolic_bp": 78.0,
                "diastolic_bp": 45.0,
                "mean_arterial_pressure": 56.0,
                "respiratory_rate": 32.0,
                "temperature": 39.5,
                "spo2": 87.0
            },
            "labs": {
                "wbc": 24800.0,
                "platelet_count": 62000.0,
                "creatinine": 3.8,
                "bilirubin": 3.2,
                "lactate": 5.8,
                "procalcitonin": 18.7,
                "crp": 285.0
            },
            "sofa_score": {
                "respiration": 3,
                "coagulation": 2,
                "liver": 2,
                "cardiovascular": 3,
                "cns": 1,
                "renal": 3,
                "total": 14
            },
            "model_prediction": {
                "sepsis_probability": 0.96,
                "risk_level": "CRITICAL",
                "confidence": 0.97,
                "feature_importance": {
                    "lactate": 0.22,
                    "sofa_total": 0.19,
                    "map": 0.16,
                    "procalcitonin": 0.14,
                    "platelet_count": 0.12
                }
            },
            "clinical_notes": "72-year-old male in septic shock. On norepinephrine. Suspected intra-abdominal source. CT abdomen shows possible bowel perforation. Surgical consult obtained."
        }
    ]
    
    output_dir = Path(__file__).parent.parent / "data" / "test_patients"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for patient in patients:
        filename = f"{patient['patient_id']}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(patient, f, indent=2)
        
        print(f"Created: {filepath}")
    
    combined_file = output_dir / "all_patients.json"
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(patients, f, indent=2)
    
    print(f"\nCreated combined file: {combined_file}")
    print(f"\n Successfully created {len(patients)} test patient files")

if __name__ == "__main__":
    create_test_patients()
