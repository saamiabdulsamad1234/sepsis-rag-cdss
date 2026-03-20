import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from rag_engine.document_loader import DocumentLoader
from rag_engine.vector_store import VectorStoreManager
from config.settings import settings

def create_sample_guidelines():
    guidelines_dir = Path(__file__).parent.parent / "data" / "guidelines"
    guidelines_dir.mkdir(parents=True, exist_ok=True)
    
    surviving_sepsis = """
# Surviving Sepsis Campaign: International Guidelines for Management of Sepsis and Septic Shock 2021

## Executive Summary

The Surviving Sepsis Campaign (SSC) guidelines provide evidence-based recommendations for the management of sepsis and septic shock.

## Key Recommendations

### Initial Resuscitation

1. **Fluid Resuscitation**: For adults with sepsis or septic shock, we recommend administering at least 30 mL/kg of IV crystalloid fluid within the first 3 hours.

2. **Vasopressors**: For patients who remain hypotensive during or after fluid resuscitation, we recommend norepinephrine as the first-choice vasopressor.

3. **Target MAP**: We recommend targeting a mean arterial pressure (MAP) of 65 mmHg in patients with septic shock requiring vasopressors.

### Antimicrobial Therapy

1. **Timing**: We recommend administration of IV antimicrobials within 1 hour of recognition of sepsis and septic shock.

2. **Empiric Therapy**: Empiric broad-spectrum therapy with one or more antimicrobials should cover all likely pathogens.

3. **De-escalation**: Antimicrobial therapy should be de-escalated based on clinical response and microbiology results.

### Source Control

1. **Timing**: Specific anatomical diagnosis and source control intervention should be sought and implemented as soon as possible.

2. **Intervention**: Remove intravascular access devices if they are a possible source of sepsis.

### Corticosteroids

1. We suggest NOT using IV hydrocortisone to treat septic shock patients if adequate fluid resuscitation and vasopressor therapy restore hemodynamic stability.

2. If this is not achievable, we suggest IV hydrocortisone at a dose of 200 mg per day.

### Blood Product Administration

1. **Transfusion Threshold**: We recommend a restrictive transfusion strategy (Hb < 7 g/dL) in adults without tissue hypoperfusion, coronary artery disease, or acute hemorrhage.

2. **Platelets**: Prophylactic platelet transfusion is suggested when counts are <10,000/mm³ in the absence of bleeding or <20,000/mm³ if there is significant bleeding risk.

### Mechanical Ventilation

1. **Tidal Volume**: We recommend using a tidal volume of 6 mL/kg predicted body weight in adults with sepsis-induced ARDS.

2. **PEEP**: We recommend using higher rather than lower PEEP in adults with sepsis-induced moderate-severe ARDS.

3. **Prone Positioning**: We recommend prone positioning for ≥12 hours per day in adults with sepsis-induced ARDS and PaO2/FiO2 ratio <150.

### Glucose Control

1. We recommend initiating insulin therapy at a threshold ≤180 mg/dL with a target range of 144-180 mg/dL.

### Nutrition

1. We recommend against the administration of parenteral nutrition alone or in combination with enteral feeds in the first 7 days.

2. We suggest starting early enteral nutrition within 72 hours rather than complete fasting.

## SOFA Score Components

The Sequential Organ Failure Assessment (SOFA) score is used to track organ dysfunction:

- **Respiration**: PaO2/FiO2 ratio
  - ≥400: 0 points
  - <400: 1 point
  - <300: 2 points
  - <200 with respiratory support: 3 points
  - <100 with respiratory support: 4 points

- **Coagulation**: Platelet count (×10³/μL)
  - ≥150: 0 points
  - <150: 1 point
  - <100: 2 points
  - <50: 3 points
  - <20: 4 points

- **Liver**: Bilirubin (mg/dL)
  - <1.2: 0 points
  - 1.2-1.9: 1 point
  - 2.0-5.9: 2 points
  - 6.0-11.9: 3 points
  - ≥12.0: 4 points

- **Cardiovascular**: Mean arterial pressure OR administration of vasopressors
  - MAP ≥70 mmHg: 0 points
  - MAP <70 mmHg: 1 point
  - Dopamine ≤5 or dobutamine (any dose): 2 points
  - Dopamine >5, epinephrine ≤0.1, or norepinephrine ≤0.1: 3 points
  - Dopamine >15, epinephrine >0.1, or norepinephrine >0.1: 4 points

- **CNS**: Glasgow Coma Scale
  - 15: 0 points
  - 13-14: 1 point
  - 10-12: 2 points
  - 6-9: 3 points
  - <6: 4 points

- **Renal**: Creatinine (mg/dL) or urine output
  - <1.2: 0 points
  - 1.2-1.9: 1 point
  - 2.0-3.4: 2 points
  - 3.5-4.9 or <500 mL/day: 3 points
  - ≥5.0 or <200 mL/day: 4 points

A SOFA score of 2 or more indicates organ dysfunction. Higher scores correlate with increased mortality.
"""
    
    qsofa_guide = """
# Quick SOFA (qSOFA) Criteria

## Purpose
The qSOFA is a bedside tool to identify patients at higher risk of poor outcomes outside the ICU.

## Criteria (1 point each)

1. **Respiratory rate** ≥22 breaths per minute
2. **Altered mentation** (GCS <15)
3. **Systolic blood pressure** ≤100 mmHg

## Interpretation

- **Score ≥2**: Suggests greater risk of poor outcome
- **Score <2**: Lower risk, but does not exclude sepsis

## Important Notes

- qSOFA is NOT a diagnostic tool for sepsis
- It is a screening tool to identify patients who may need closer monitoring
- A qSOFA score ≥2 should prompt consideration of possible infection and organ dysfunction
- Patients with qSOFA ≥2 should have SOFA score calculated

## Clinical Application

When a patient has qSOFA ≥2:
1. Assess for suspected or confirmed infection
2. Calculate full SOFA score
3. Initiate sepsis bundle if appropriate
4. Consider ICU consultation
5. Implement frequent reassessment

## Limitations

- Less sensitive than SOFA for identifying sepsis
- Should not be used as a single screening tool
- Most useful in non-ICU settings
- May miss patients with early sepsis
"""
    
    sepsis_definition = """
# Sepsis-3 Definitions

## Sepsis
Life-threatening organ dysfunction caused by a dysregulated host response to infection.

### Clinical Criteria
- Suspected or documented infection
- Acute increase in SOFA score ≥2 points

### Organ Dysfunction
Indicates a substantially increased risk of hospital mortality (>10%)

## Septic Shock
Subset of sepsis with particularly profound circulatory, cellular, and metabolic abnormalities.

### Clinical Criteria
Sepsis with:
1. Vasopressor therapy needed to maintain MAP ≥65 mmHg
2. Serum lactate >2 mmol/L (18 mg/dL)

Both criteria must be present DESPITE adequate fluid resuscitation.

### Mortality Risk
Associated with hospital mortality >40%

## Key Changes from Sepsis-2

1. **Removed SIRS criteria**: Not required for sepsis diagnosis
2. **Emphasis on organ dysfunction**: SOFA score ≥2 required
3. **Septic shock redefined**: Requires both hypotension needing vasopressors AND lactate >2 mmol/L
4. **Removed "severe sepsis"**: Now just sepsis or septic shock

## Biomarkers

### Lactate
- Normal: <2 mmol/L
- Elevated: ≥2 mmol/L (suggests tissue hypoperfusion)
- Persistently elevated: Associated with worse outcomes
- Serial measurements recommended

### Procalcitonin
- Normal: <0.1 ng/mL
- Possible bacterial infection: 0.1-0.5 ng/mL
- Likely bacterial infection: >0.5 ng/mL
- Severe sepsis/shock: Often >2 ng/mL
- Useful for antibiotic stewardship

## Time-Sensitive Interventions

### Hour-1 Bundle
1. Measure lactate level
2. Obtain blood cultures before antibiotics
3. Administer broad-spectrum antibiotics
4. Begin rapid administration of 30 mL/kg crystalloid for hypotension or lactate ≥4 mmol/L
5. Apply vasopressors if hypotensive during or after fluid resuscitation to maintain MAP ≥65 mmHg
"""
    
    antibiotic_guide = """
# Empiric Antibiotic Selection in Sepsis

## General Principles

1. **Timing is Critical**: Antibiotics should be administered within 1 hour of sepsis recognition
2. **Broad Spectrum**: Initial therapy should cover all likely pathogens
3. **Source Matters**: Consider likely source of infection
4. **Patient Factors**: Consider patient's immune status, recent antibiotic use, local resistance patterns

## Community-Acquired Infections

### Pneumonia
- **First-line**: Ceftriaxone + Azithromycin OR Fluoroquinolone
- **Severe**: Add vancomycin if MRSA risk factors

### Urinary Tract
- **First-line**: Ceftriaxone OR Fluoroquinolone
- **Complicated**: Piperacillin-tazobactam OR Carbapenem

### Intra-abdominal
- **First-line**: Piperacillin-tazobactam OR Ceftriaxone + Metronidazole
- **High-risk**: Carbapenem

### Skin/Soft Tissue
- **First-line**: Vancomycin + Piperacillin-tazobactam
- **Necrotizing**: Add clindamycin for toxin suppression

## Healthcare-Associated Infections

### Hospital-Acquired Pneumonia
- **Early (<5 days)**: Ceftriaxone
- **Late (≥5 days)**: Anti-pseudomonal beta-lactam + Vancomycin

### Catheter-Related Bloodstream
- **Empiric**: Vancomycin + Anti-pseudomonal beta-lactam

## Immunocompromised Hosts

### Neutropenic Fever
- **Empiric**: Anti-pseudomonal beta-lactam (Cefepime, Piperacillin-tazobactam, or Meropenem)
- **Add**: Vancomycin if skin/catheter source or unstable
- **Antifungal**: Consider if persistent fever >3-5 days

## De-escalation Strategy

1. **Review cultures at 48-72 hours**
2. **Narrow spectrum** based on susceptibilities
3. **Consider stopping** if cultures negative and clinical improvement
4. **Typical duration**: 7-10 days (adjust based on source and response)

## Red Flags for Resistant Organisms

- Recent antibiotic use (<90 days)
- Recent hospitalization
- Healthcare facility residence
- Immunosuppression
- Known colonization with resistant organisms
- High local resistance rates
"""
    
    fluid_management = """
# Fluid Management in Sepsis

## Initial Resuscitation

### Volume
- **Minimum**: 30 mL/kg of crystalloid within first 3 hours
- **Typical patient (70 kg)**: At least 2100 mL

### Type of Fluid

#### Crystalloids (Preferred)
- **Balanced crystalloids** (Lactated Ringer's, Plasmalyte)
  - May reduce mortality and AKI vs normal saline
  - Preferred in most situations
- **Normal Saline**
  - Alternative if balanced solutions unavailable
  - Risk of hyperchloremic acidosis with large volumes

#### Colloids
- **Albumin**: Consider if patients require substantial crystalloid volumes
- **Avoid**: Hydroxyethyl starches (increased mortality and AKI)

## Fluid Responsiveness

### Assessment Methods
1. **Passive leg raise**
2. **Pulse pressure variation** (if mechanically ventilated)
3. **Stroke volume variation** (if mechanically ventilated)
4. **Ultrasound**: IVC collapsibility, cardiac output

### Signs of Fluid Overload
- Pulmonary edema
- Increasing oxygen requirements
- Peripheral edema
- Elevated CVP

## Dynamic Assessment

### Reassess After Each Bolus
- Hemodynamic improvement?
- Lactate clearance?
- Urine output improvement?
- Signs of fluid overload?

### Continue Fluids If:
- Ongoing hypotension
- Elevated lactate
- Poor tissue perfusion
- Fluid responsive

### Stop/Slow Fluids If:
- Hemodynamically stable
- Lactate normalizing
- Signs of fluid overload
- No longer fluid responsive

## Conservative Strategy After Resuscitation

Once stabilized:
1. **Restrict maintenance fluids**
2. **Target neutral to negative fluid balance**
3. **Consider diuretics** if fluid overloaded
4. **Monitor**: Daily weights, fluid balance

## Special Populations

### Heart Failure
- **Smaller boluses** (250-500 mL)
- **Closer monitoring** for pulmonary edema
- **Early vasopressor** consideration

### Renal Failure
- **Careful volume assessment**
- **Consider RRT** if severe fluid overload

### ARDS
- **Conservative fluid strategy** after initial resuscitation
- **Target negative balance** if stable
"""
    
    guidelines = {
        "surviving_sepsis_2021.md": surviving_sepsis,
        "qsofa_criteria.md": qsofa_guide,
        "sepsis3_definitions.md": sepsis_definition,
        "antibiotic_selection.md": antibiotic_guide,
        "fluid_management.md": fluid_management
    }
    
    for filename, content in guidelines.items():
        filepath = guidelines_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created: {filepath}")
    
    return guidelines_dir

def index_documents():
    print("Creating sample clinical guidelines...")
    guidelines_dir = create_sample_guidelines()
    
    print("\nInitializing document loader...")
    loader = DocumentLoader(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )
    
    print(f"\nLoading documents from: {guidelines_dir}")
    documents = loader.load_directory(str(guidelines_dir))
    print(f"Loaded {len(documents)} document chunks")
    
    print("\nInitializing vector store...")
    vector_store = VectorStoreManager()
    
    print("Deleting existing collection...")
    vector_store.delete_collection()
    
    print("Re-initializing vector store...")
    vector_store._initialize_vectorstore()
    
    print("\nIndexing documents...")
    success = vector_store.add_documents(documents)
    
    if success:
        count = vector_store.get_collection_count()
        print(f"\n Successfully indexed {count} document chunks")
        print(f"Vector store location: {settings.chroma_persist_dir}")
    else:
        print("\n Failed to index documents")
        return False
    
    print("\nTesting retrieval...")
    test_query = "What is the SOFA score?"
    results = vector_store.similarity_search(test_query, k=3)
    
    if results:
        print(f"\n Retrieval test successful - found {len(results)} results")
        print("\nSample result:")
        print(f"Source: {results[0].metadata.get('source', 'Unknown')}")
        print(f"Content preview: {results[0].page_content[:200]}...")
    else:
        print("\n Retrieval test failed")
    
    return True

if __name__ == "__main__":
    print("=" * 80)
    print("Sepsis RAG Document Indexing")
    print("=" * 80)
    
    if not settings.openai_api_key:
        print("\n  WARNING: OPENAI_API_KEY not set in environment")
        print("Please set your API key in .env file or environment variables")
        print("\nContinuing anyway for demonstration...")
    
    success = index_documents()
    
    if success:
        print("\n" + "=" * 80)
        print(" Indexing completed successfully!")
        print("=" * 80)
        print("\nYou can now start the backend server:")
        print("  cd backend && uvicorn main:app --reload")
    else:
        print("\n" + "=" * 80)
        print(" Indexing failed")
        print("=" * 80)
