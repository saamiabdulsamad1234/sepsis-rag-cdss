import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

class MIMICToRAGConverter:
    """Converts MIMIC patient data to RAG-compatible JSON format."""
    
    def __init__(self, output_dir: str = "data/mimic_patients"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def convert_patient(
        self,
        patient_id: str,
        vitals_df: pd.DataFrame,
        labs_df: pd.DataFrame,
        sofa_components: Dict[str, int],
        model_prediction: Dict[str, Any],
        demographics: Optional[Dict] = None,
        clinical_notes: Optional[str] = None
    ) -> Dict:
        """Convert MIMIC patient data to RAG-compatible dict."""
        
        vitals = self._aggregate_vitals(vitals_df)
        labs = self._aggregate_labs(labs_df)
        
        patient_data = {
            "patient_id": str(patient_id),
            "age": demographics.get('age') if demographics else None,
            "gender": self._normalize_gender(demographics.get('gender')) if demographics else None,
            "admission_time": datetime.now().isoformat(),
            "vitals": vitals,
            "labs": labs,
            "sofa_score": {
                "respiration": int(sofa_components.get('respiration', 0)),
                "coagulation": int(sofa_components.get('coagulation', 0)),
                "liver": int(sofa_components.get('liver', 0)),
                "cardiovascular": int(sofa_components.get('cardiovascular', 0)),
                "cns": int(sofa_components.get('cns', 0)),
                "renal": int(sofa_components.get('renal', 0)),
                "total": sum(sofa_components.values())
            },
            "model_prediction": {
                "sepsis_probability": float(model_prediction.get('probability', 0)),
                "risk_level": str(model_prediction.get('risk_level', 'MODERATE')),
                "confidence": float(model_prediction.get('confidence', 0.5)),
                "feature_importance": model_prediction.get('feature_importance', {})
            },
            "clinical_notes": clinical_notes or f"MIMIC patient {patient_id}"
        }
        
        return patient_data
    
    def _aggregate_vitals(self, vitals_df: pd.DataFrame) -> Dict:
        
        if vitals_df.empty:
            return self._get_default_vitals()
        
        def safe_get(column, default=None):
            if column in vitals_df.columns:
                values = vitals_df[column].dropna()
                if len(values) > 0:
                    return float(values.iloc[-1])
            return default
        
        return {
            "heart_rate": safe_get('heart_rate') or safe_get('hr'),
            "systolic_bp": safe_get('systolic_bp') or safe_get('sbp'),
            "diastolic_bp": safe_get('diastolic_bp') or safe_get('dbp'),
            "mean_arterial_pressure": safe_get('mean_arterial_pressure') or safe_get('map') or safe_get('mbp'),
            "respiratory_rate": safe_get('respiratory_rate') or safe_get('resp_rate') or safe_get('rr'),
            "temperature": safe_get('temperature') or safe_get('temp'),
            "spo2": safe_get('spo2') or safe_get('o2sat')
        }
    
    def _aggregate_labs(self, labs_df: pd.DataFrame) -> Dict:
        
        if labs_df.empty:
            return self._get_default_labs()
        
        def safe_get(column, default=None):
            if column in labs_df.columns:
                values = labs_df[column].dropna()
                if len(values) > 0:
                    return float(values.iloc[-1])
            return default
        
        return {
            "wbc": safe_get('wbc') or safe_get('white_blood_cells'),
            "platelet_count": safe_get('platelet_count') or safe_get('platelet') or safe_get('platelets'),
            "creatinine": safe_get('creatinine') or safe_get('creat'),
            "bilirubin": safe_get('bilirubin') or safe_get('bili'),
            "lactate": safe_get('lactate'),
            "procalcitonin": safe_get('procalcitonin') or safe_get('pct'),
            "crp": safe_get('crp') or safe_get('c_reactive_protein')
        }
    
    def _normalize_gender(self, gender: str) -> str:
        if not gender:
            return None
        
        gender = str(gender).upper()
        if gender in ['M', 'MALE', '1']:
            return 'Male'
        elif gender in ['F', 'FEMALE', '2', '0']:
            return 'Female'
        else:
            return 'Unknown'
    
    def _get_default_vitals(self) -> Dict:
        return {
            "heart_rate": None,
            "systolic_bp": None,
            "diastolic_bp": None,
            "mean_arterial_pressure": None,
            "respiratory_rate": None,
            "temperature": None,
            "spo2": None
        }
    
    def _get_default_labs(self) -> Dict:
        return {
            "wbc": None,
            "platelet_count": None,
            "creatinine": None,
            "bilirubin": None,
            "lactate": None,
            "procalcitonin": None,
            "crp": None
        }
    
    def save_patient(self, patient_data: Dict, filename: Optional[str] = None) -> str:
        
        if filename is None:
            filename = f"{patient_data['patient_id']}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(patient_data, f, indent=2)
        
        print(f" Saved patient {patient_data['patient_id']} to {filepath}")
        return str(filepath)
    
    def batch_convert(
        self,
        patients_df: pd.DataFrame,
        vitals_df: pd.DataFrame,
        labs_df: pd.DataFrame,
        sofa_df: pd.DataFrame,
        predictions_df: pd.DataFrame,
        patient_id_col: str = 'subject_id',
        max_patients: int = 10
    ) -> List[str]:
        """Batch convert multiple patients from MIMIC DataFrames."""
        
        saved_files = []
        
        patient_ids = patients_df[patient_id_col].unique()[:max_patients]
        
        for patient_id in patient_ids:
            try:
                patient_vitals = vitals_df[vitals_df[patient_id_col] == patient_id]
                patient_labs = labs_df[labs_df[patient_id_col] == patient_id]
                patient_sofa = sofa_df[sofa_df[patient_id_col] == patient_id].iloc[0] if patient_id in sofa_df[patient_id_col].values else {}
                patient_pred = predictions_df[predictions_df[patient_id_col] == patient_id].iloc[0] if patient_id in predictions_df[patient_id_col].values else {}
                patient_demo = patients_df[patients_df[patient_id_col] == patient_id].iloc[0]
                
                sofa_components = {
                    'respiration': patient_sofa.get('sofa_respiration', 0),
                    'coagulation': patient_sofa.get('sofa_coagulation', 0),
                    'liver': patient_sofa.get('sofa_liver', 0),
                    'cardiovascular': patient_sofa.get('sofa_cardiovascular', 0),
                    'cns': patient_sofa.get('sofa_cns', 0),
                    'renal': patient_sofa.get('sofa_renal', 0)
                }
                
                model_prediction = {
                    'probability': patient_pred.get('sepsis_probability', 0.5),
                    'risk_level': patient_pred.get('risk_level', 'MODERATE'),
                    'confidence': patient_pred.get('confidence', 0.7),
                    'feature_importance': patient_pred.get('feature_importance', {})
                }
                
                demographics = {
                    'age': patient_demo.get('age'),
                    'gender': patient_demo.get('gender')
                }
                
                patient_data = self.convert_patient(
                    patient_id=patient_id,
                    vitals_df=patient_vitals,
                    labs_df=patient_labs,
                    sofa_components=sofa_components,
                    model_prediction=model_prediction,
                    demographics=demographics
                )
                
                filepath = self.save_patient(patient_data)
                saved_files.append(filepath)
                
            except Exception as e:
                print(f" Error converting patient {patient_id}: {e}")
                continue
        
        print(f"\n Converted {len(saved_files)} patients successfully")
        return saved_files


def example_usage_single_patient():
    
    converter = MIMICToRAGConverter(output_dir="../sepsis_rag_v2/data/mimic_patients")
    
    vitals = pd.DataFrame({
        'charttime': ['2024-01-01 10:00:00'],
        'heart_rate': [118.0],
        'sbp': [92.0],
        'dbp': [58.0],
        'map': [69.0],
        'resp_rate': [28.0],
        'temperature': [38.8],
        'spo2': [91.0]
    })
    
    labs = pd.DataFrame({
        'charttime': ['2024-01-01 10:00:00'],
        'wbc': [18500.0],
        'platelet': [95000.0],
        'creatinine': [2.4],
        'bilirubin': [1.8],
        'lactate': [3.2],
        'procalcitonin': [8.5],
        'crp': [185.0]
    })
    
    sofa_components = {
        'respiration': 2,
        'coagulation': 1,
        'liver': 1,
        'cardiovascular': 2,
        'cns': 0,
        'renal': 2
    }
    
    model_prediction = {
        'probability': 0.87,
        'risk_level': 'HIGH',
        'confidence': 0.92,
        'feature_importance': {
            'lactate': 0.18,
            'heart_rate': 0.15,
            'sofa_total': 0.14,
            'procalcitonin': 0.12,
            'map': 0.11
        }
    }
    
    demographics = {
        'age': 67,
        'gender': 'M'
    }
    
    patient_data = converter.convert_patient(
        patient_id="MIMIC-12345",
        vitals_df=vitals,
        labs_df=labs,
        sofa_components=sofa_components,
        model_prediction=model_prediction,
        demographics=demographics,
        clinical_notes="67-year-old male with suspected pneumonia"
    )
    
    converter.save_patient(patient_data)
    
    return patient_data


if __name__ == "__main__":
    print("MIMIC-III/IV to RAG Converter")
    print("=" * 50)
    print("\nExample usage:")
    patient = example_usage_single_patient()
    print(f"\n Example patient exported: {patient['patient_id']}")
    print(f"   Risk Level: {patient['model_prediction']['risk_level']}")
    print(f"   Sepsis Probability: {patient['model_prediction']['sepsis_probability']:.1%}")
