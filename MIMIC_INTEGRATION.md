# MIMIC Data Integration Guide

## How to Connect Your Jupyter Notebook to the RAG System

This guide shows you how to export patients from your MIMIC-based sepsis prediction notebook and load them into the RAG system.

---

##  Quick Start (3 Steps)

### Step 1: Add to Your Jupyter Notebook

At the end of your notebook, after running predictions, add this code:

```python
import sys
sys.path.append('../sepsis_rag_v2/scripts')
from mimic_integration import MIMICToRAGConverter

# Initialize converter
converter = MIMICToRAGConverter(output_dir='../sepsis_rag_v2/data/mimic_patients')
```

### Step 2: Convert Patients

```python
# For each patient you want to export
patient_data = converter.convert_patient(
    patient_id=str(subject_id),  # Your MIMIC subject_id or hadm_id
    vitals_df=patient_vitals,    # DataFrame with vitals (last 24h or aggregated)
    labs_df=patient_labs,        # DataFrame with labs
    sofa_components=sofa_dict,   # Your calculated SOFA scores
    model_prediction={
        'probability': y_pred_proba,      # From your model
        'risk_level': risk_tier,          # 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'
        'confidence': confidence_score,
        'feature_importance': feat_imp_dict
    },
    demographics={
        'age': age,
        'gender': gender
    },
    clinical_notes=f"MIMIC patient {subject_id}"
)

# Save to file
converter.save_patient(patient_data)
```

### Step 3: Load in RAG System

```bash
# Start the RAG system
cd sepsis_rag_v2
./start.sh

# Your MIMIC patients will appear in the UI!
```

---

##  Detailed Integration Examples

### Example 1: Single Patient Export

```python
import pandas as pd
import numpy as np
from mimic_integration import MIMICToRAGConverter

# Initialize
converter = MIMICToRAGConverter(output_dir='../sepsis_rag_v2/data/mimic_patients')

# Prepare vitals (use your actual data)
vitals = pd.DataFrame({
    'charttime': patient_vitals['charttime'],
    'heart_rate': patient_vitals['heart_rate'],
    'sbp': patient_vitals['sbp'],
    'dbp': patient_vitals['dbp'],
    'map': patient_vitals['map'],
    'resp_rate': patient_vitals['resp_rate'],
    'temperature': patient_vitals['temperature'],
    'spo2': patient_vitals['spo2']
})

# Prepare labs (use your actual data)
labs = pd.DataFrame({
    'charttime': patient_labs['charttime'],
    'wbc': patient_labs['wbc'],
    'platelet': patient_labs['platelet'],
    'creatinine': patient_labs['creatinine'],
    'bilirubin': patient_labs['bilirubin'],
    'lactate': patient_labs['lactate'],
    'procalcitonin': patient_labs.get('procalcitonin'),  # May not exist in MIMIC
    'crp': patient_labs.get('crp')
})

# SOFA components (from your calculation)
sofa = {
    'respiration': sofa_resp,
    'coagulation': sofa_coag,
    'liver': sofa_liver,
    'cardiovascular': sofa_cardio,
    'cns': sofa_cns,
    'renal': sofa_renal
}

# Model prediction (from your ML model)
prediction = {
    'probability': float(model.predict_proba(X_patient)[0][1]),
    'risk_level': classify_risk(y_pred),  # Your risk classification function
    'confidence': float(confidence),
    'feature_importance': dict(zip(feature_names, model.feature_importances_))
}

# Demographics
demo = {
    'age': int(patient_age),
    'gender': patient_gender  # 'M' or 'F'
}

# Convert and save
patient_data = converter.convert_patient(
    patient_id=f"MIMIC-{subject_id}",
    vitals_df=vitals,
    labs_df=labs,
    sofa_components=sofa,
    model_prediction=prediction,
    demographics=demo,
    clinical_notes=f"MIMIC-III patient {subject_id}, admission {hadm_id}"
)

filepath = converter.save_patient(patient_data)
print(f" Saved to: {filepath}")
```

---

### Example 2: Batch Export (Multiple Patients)

```python
from mimic_integration import MIMICToRAGConverter

converter = MIMICToRAGConverter(output_dir='../sepsis_rag_v2/data/mimic_patients')

# Export top 10 high-risk patients
high_risk_patients = predictions_df[predictions_df['risk_level'] == 'HIGH'].head(10)

for idx, row in high_risk_patients.iterrows():
    subject_id = row['subject_id']
    
    # Get patient data
    patient_vitals = vitals_df[vitals_df['subject_id'] == subject_id]
    patient_labs = labs_df[labs_df['subject_id'] == subject_id]
    patient_sofa = sofa_df[sofa_df['subject_id'] == subject_id].iloc[0]
    patient_demo = demographics_df[demographics_df['subject_id'] == subject_id].iloc[0]
    
    # Convert
    patient_data = converter.convert_patient(
        patient_id=f"MIMIC-{subject_id}",
        vitals_df=patient_vitals,
        labs_df=patient_labs,
        sofa_components={
            'respiration': int(patient_sofa['sofa_respiration']),
            'coagulation': int(patient_sofa['sofa_coagulation']),
            'liver': int(patient_sofa['sofa_liver']),
            'cardiovascular': int(patient_sofa['sofa_cardiovascular']),
            'cns': int(patient_sofa['sofa_cns']),
            'renal': int(patient_sofa['sofa_renal'])
        },
        model_prediction={
            'probability': float(row['sepsis_probability']),
            'risk_level': str(row['risk_level']),
            'confidence': float(row['confidence']),
            'feature_importance': eval(row['feature_importance'])  # If stored as string
        },
        demographics={
            'age': int(patient_demo['age']),
            'gender': str(patient_demo['gender'])
        }
    )
    
    converter.save_patient(patient_data)

print(" Batch export complete!")
```

---

### Example 3: Direct From Notebook Variables

If you have everything in memory from your notebook:

```python
from mimic_integration import MIMICToRAGConverter

converter = MIMICToRAGConverter(output_dir='../sepsis_rag_v2/data/mimic_patients')

# Assuming you have these variables from your analysis:
# - hr, sbp, dbp, map_val, rr, temp, spo2 (vitals)
# - wbc, plt, creat, bili, lac, pct, crp (labs)
# - sofa_resp, sofa_coag, sofa_liver, sofa_cardio, sofa_cns, sofa_renal
# - y_pred_proba, risk_level, model_confidence
# - patient_age, patient_gender, subject_id

import pandas as pd

# Create DataFrames from your variables
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
    'platelet': [plt],
    'creatinine': [creat],
    'bilirubin': [bili],
    'lactate': [lac],
    'procalcitonin': [pct] if pct else [None],
    'crp': [crp] if crp else [None]
})

patient_data = converter.convert_patient(
    patient_id=f"MIMIC-{subject_id}",
    vitals_df=vitals_df,
    labs_df=labs_df,
    sofa_components={
        'respiration': sofa_resp,
        'coagulation': sofa_coag,
        'liver': sofa_liver,
        'cardiovascular': sofa_cardio,
        'cns': sofa_cns,
        'renal': sofa_renal
    },
    model_prediction={
        'probability': y_pred_proba,
        'risk_level': risk_level,
        'confidence': model_confidence,
        'feature_importance': feature_importances
    },
    demographics={
        'age': patient_age,
        'gender': patient_gender
    },
    clinical_notes=f"MIMIC patient with sepsis probability {y_pred_proba:.1%}"
)

converter.save_patient(patient_data)
```

---

##  Handling Different Data Formats

### If Your Column Names Are Different

The converter handles common variations automatically:

```python
# These all work:
'heart_rate' or 'hr'
'systolic_bp' or 'sbp'
'diastolic_bp' or 'dbp'
'mean_arterial_pressure' or 'map' or 'mbp'
'respiratory_rate' or 'resp_rate' or 'rr'
'temperature' or 'temp'
'spo2' or 'o2sat'

'wbc' or 'white_blood_cells'
'platelet_count' or 'platelet' or 'platelets'
'creatinine' or 'creat'
'bilirubin' or 'bili'
'procalcitonin' or 'pct'
'crp' or 'c_reactive_protein'
```

### If You Have Time-Series Data

The converter uses the **last value** from your DataFrame:

```python
# If you have 24 hours of vitals
vitals_24h = pd.DataFrame({
    'charttime': ['2024-01-01 08:00', '2024-01-01 12:00', '2024-01-01 16:00', ...],
    'heart_rate': [110, 115, 118, ...],
    'sbp': [100, 95, 92, ...],
    ...
})

# Converter automatically uses the most recent values (last row)
patient_data = converter.convert_patient(
    patient_id="MIMIC-123",
    vitals_df=vitals_24h,  # Full time series
    ...
)
```

### If You Want to Aggregate Differently

```python
# Use mean instead of last value
vitals_mean = vitals_24h.mean().to_frame().T
vitals_mean['charttime'] = vitals_24h['charttime'].iloc[-1]

patient_data = converter.convert_patient(
    patient_id="MIMIC-123",
    vitals_df=vitals_mean,
    ...
)
```

---

##  Complete Workflow Example

Here's the complete workflow from notebook to RAG:

```python
# ==========================================
# In Your Jupyter Notebook
# ==========================================

# 1. Import the converter
import sys
sys.path.append('../sepsis_rag_v2/scripts')
from mimic_integration import MIMICToRAGConverter

# 2. Initialize
converter = MIMICToRAGConverter(output_dir='../sepsis_rag_v2/data/mimic_patients')

# 3. After running your model on MIMIC data
for subject_id in high_risk_patients['subject_id']:
    
    # Get patient data (your existing code)
    patient_vitals = get_patient_vitals(subject_id)  # Your function
    patient_labs = get_patient_labs(subject_id)      # Your function
    patient_sofa = calculate_sofa(subject_id)        # Your function
    
    # Get model prediction (your existing code)
    X_patient = prepare_features(subject_id)         # Your function
    y_pred_proba = model.predict_proba(X_patient)[0][1]
    risk_level = classify_risk(y_pred_proba)         # Your function
    
    # Convert and export
    patient_data = converter.convert_patient(
        patient_id=f"MIMIC-{subject_id}",
        vitals_df=patient_vitals,
        labs_df=patient_labs,
        sofa_components=patient_sofa,
        model_prediction={
            'probability': y_pred_proba,
            'risk_level': risk_level,
            'confidence': 0.85,  # Or calculate from your model
            'feature_importance': dict(zip(feature_names, model.feature_importances_))
        },
        demographics={
            'age': get_patient_age(subject_id),
            'gender': get_patient_gender(subject_id)
        },
        clinical_notes=f"MIMIC-III patient {subject_id}"
    )
    
    # Save
    converter.save_patient(patient_data)
    print(f" Exported patient {subject_id}")

print("\n All patients exported!")
```

```bash
# ==========================================
# In Terminal
# ==========================================

# 4. Start the RAG system
cd sepsis_rag_v2
./start.sh

# 5. Open browser: http://localhost:8501
# 6. Your MIMIC patients are now available!
```

---

##  What Gets Exported

For each patient, the RAG system gets:

```json
{
  "patient_id": "MIMIC-12345",
  "age": 67,
  "gender": "Male",
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
      "sofa_total": 0.14
    }
  },
  "clinical_notes": "MIMIC-III patient 12345"
}
```

---

##  Troubleshooting

### Missing Columns

If you get errors about missing columns:

```python
# Check what columns you have
print(vitals_df.columns)
print(labs_df.columns)

# The converter will set missing values to None automatically
# So it's OK if some labs (like procalcitonin) don't exist in MIMIC
```

### Type Errors

Make sure your values are the right type:

```python
# Convert to proper types
patient_data = converter.convert_patient(
    patient_id=str(subject_id),          # String
    vitals_df=vitals_df,                 # DataFrame
    labs_df=labs_df,                     # DataFrame
    sofa_components={                     # Dict with ints
        'respiration': int(sofa_resp),
        'coagulation': int(sofa_coag),
        ...
    },
    model_prediction={                    # Dict with floats/string
        'probability': float(y_pred),
        'risk_level': str(risk),
        'confidence': float(conf),
        'feature_importance': dict(feat_imp)
    },
    demographics={                        # Dict
        'age': int(age),
        'gender': str(gender)
    }
)
```

### Files Not Showing in UI

Make sure files are saved to the correct directory:

```python
# Correct path (relative to notebook location)
converter = MIMICToRAGConverter(output_dir='../sepsis_rag_v2/data/mimic_patients')

# Check files were created
import os
print(os.listdir('../sepsis_rag_v2/data/mimic_patients'))
```

---

##  Verification

After exporting, verify your patients:

```python
import json

# Load and check
with open('../sepsis_rag_v2/data/mimic_patients/MIMIC-12345.json', 'r') as f:
    patient = json.load(f)
    
print(f"Patient ID: {patient['patient_id']}")
print(f"Age: {patient['age']}")
print(f"Risk Level: {patient['model_prediction']['risk_level']}")
print(f"Sepsis Probability: {patient['model_prediction']['sepsis_probability']:.1%}")
print(f"SOFA Total: {patient['sofa_score']['total']}")
```

---

##  For Your Professor Demo

1. **Show your Jupyter notebook** running on MIMIC data
2. **Export a high-risk patient** using the converter
3. **Switch to RAG system** (http://localhost:8501)
4. **Load the MIMIC patient** you just exported
5. **Show AI analysis** explaining why they're high risk
6. **Interactive chat**: "What should I do for this patient?"

**This demonstrates the complete pipeline: Real MIMIC data → ML prediction → AI explanation**

---

##  Summary

```python
# Minimal example - copy this into your notebook

from mimic_integration import MIMICToRAGConverter
import pandas as pd

converter = MIMICToRAGConverter(output_dir='../sepsis_rag_v2/data/mimic_patients')

# Prepare your data as DataFrames
vitals = pd.DataFrame({...})  # Your vitals
labs = pd.DataFrame({...})    # Your labs

# Convert and save
patient_data = converter.convert_patient(
    patient_id="MIMIC-12345",
    vitals_df=vitals,
    labs_df=labs,
    sofa_components={'respiration': 2, ...},
    model_prediction={'probability': 0.87, 'risk_level': 'HIGH', ...},
    demographics={'age': 67, 'gender': 'M'}
)

converter.save_patient(patient_data)
```

Now your real MIMIC patients will appear in the RAG system! 
