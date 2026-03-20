# Sepsis Prediction System v2.0 - LLM-Powered RAG Clinical Decision Support

##  Overview

This is an **experimental** LLM-RAG (Large Language Model - Retrieval Augmented Generation) layer built on top of the sepsis prediction model. It provides intelligent clinical decision support through:

-  **AI-powered patient analysis** with step-by-step clinical reasoning
-  **Interactive chat interface** for querying patient data and guidelines
-  **RAG-based guideline retrieval** from Surviving Sepsis Campaign and SOFA scoring
-  **Explainable AI** showing reasoning chains and evidence citations

** DISCLAIMER: This is an experimental educational tool. NOT for clinical use.**

---

##  Architecture

```
sepsis_rag_v2/
 backend/              # FastAPI REST API
    main.py          # API endpoints
 frontend/            # Streamlit UI
    app.py          # Interactive dashboard
 rag_engine/          # RAG pipeline core
    document_loader.py   # PDF/Markdown ingestion
    vector_store.py      # ChromaDB vector database
    reasoning.py         # LLM reasoning engine
    prompts.py          # Clinical prompt templates
    pipeline.py         # Main RAG orchestrator
 models/              # Pydantic data models
    schemas.py      # Patient context, predictions, responses
 config/              # Configuration
    settings.py     # Environment settings
 data/
    guidelines/     # Clinical guideline documents
    test_patients/  # Example patient JSONs
 scripts/
    index_documents.py     # Index clinical guidelines
    create_test_patients.py # Generate test data
 tests/              # Unit tests
```

---

##  Quick Start

### 1. Prerequisites

- Python 3.9+
- OpenAI API key (or Anthropic API key)

### 2. Installation

```bash
cd sepsis_rag_v2
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the project root:

```bash
cp .env.template .env
```

Edit `.env` and add your API key:

```
OPENAI_API_KEY=sk-your-key-here
MODEL_NAME=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small
```

### 4. Index Clinical Guidelines

```bash
python scripts/index_documents.py
```

This creates sample clinical guidelines and indexes them into ChromaDB.

### 5. Start the Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

### 6. Start the Frontend

In a new terminal:

```bash
streamlit run frontend/app.py
```

Frontend will open at: `http://localhost:8501`

---

##  Usage

### Loading Demo Patients

1. Click **"Load Demo Patient"** in the sidebar
2. View patient vitals, labs, SOFA score, and model predictions

### Clinical Analysis

1. Navigate to **"Clinical Analysis"** tab
2. Click **"Generate Clinical Analysis"**
3. Review:
   - AI-generated summary
   - Key findings
   - Risk factors
   - Evidence-based recommendations
   - Step-by-step reasoning

### Chat Assistant

1. Navigate to **"Chat Assistant"** tab
2. Ask questions like:
   - "Why is this patient high risk?"
   - "What antibiotics should I consider?"
   - "Explain the SOFA score components"
   - "What are the next steps for management?"
3. View retrieved guidelines and reasoning steps

---

##  API Endpoints

### Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "vector_store": "connected",
  "documents_loaded": 25
}
```

### Analyze Patient
```bash
POST /analyze_patient
```

Request:
```json
{
  "patient_context": {
    "patient_id": "PT-001",
    "vitals": {...},
    "labs": {...},
    "sofa_score": {...},
    "model_prediction": {...}
  }
}
```

Response:
```json
{
  "summary": "Patient presents with...",
  "key_findings": [...],
  "risk_factors": [...],
  "recommendations": [...],
  "urgency_level": "HIGH",
  "reasoning": "..."
}
```

### Chat
```bash
POST /chat
```

Request:
```json
{
  "patient_context": {...},
  "question": "Why is lactate elevated?",
  "chat_history": []
}
```

Response:
```json
{
  "answer": "Elevated lactate suggests...",
  "retrieved_documents": [...],
  "reasoning_chain": [...],
  "confidence": 0.85,
  "citations": ["Surviving Sepsis Campaign 2021"]
}
```

---

##  Testing with Sample Data

### Create Test Patients

```bash
python scripts/create_test_patients.py
```

This generates 3 test patients:
- **PT-HIGH-001**: High-risk sepsis with pneumonia
- **PT-MODERATE-002**: Moderate-risk UTI
- **PT-CRITICAL-003**: Critical septic shock

### Load Patient Data

```python
import json

with open('data/test_patients/PT-HIGH-001.json', 'r') as f:
    patient = json.load(f)
```

---

##  How RAG Works

### 1. Document Ingestion
- Clinical guidelines (Surviving Sepsis, SOFA criteria, etc.) are loaded
- Text is chunked into semantic segments
- Each chunk is embedded using OpenAI embeddings
- Embeddings stored in ChromaDB vector database

### 2. Query Processing
- User asks a question about a patient
- Question + patient context → search query
- Top-k most relevant guideline chunks retrieved

### 3. LLM Reasoning
- Patient summary + retrieved guidelines + question → prompt
- LLM generates response with clinical reasoning
- Response includes:
  - Direct answer
  - Step-by-step reasoning chain
  - Citations to source guidelines
  - Confidence score

### 4. Response Enhancement
- Reasoning steps extracted
- Citations mapped to source documents
- Confidence calculated based on language patterns

---

##  Included Clinical Guidelines

1. **Surviving Sepsis Campaign 2021**
   - Initial resuscitation protocols
   - Antimicrobial therapy timing
   - Fluid management strategies
   - Vasopressor recommendations

2. **SOFA Score Criteria**
   - Component breakdown (respiration, coagulation, liver, cardiovascular, CNS, renal)
   - Scoring thresholds
   - Mortality correlation

3. **qSOFA Quick Reference**
   - Bedside screening criteria
   - Risk stratification

4. **Sepsis-3 Definitions**
   - Updated sepsis/septic shock criteria
   - Biomarker interpretation (lactate, procalcitonin)

5. **Antibiotic Selection Guide**
   - Empiric therapy by infection source
   - De-escalation strategies
   - Resistance patterns

6. **Fluid Management**
   - Initial resuscitation volumes
   - Crystalloid vs colloid selection
   - Fluid responsiveness assessment

---

##  Configuration Options

### `config/settings.py`

```python
model_name = "gpt-4-turbo-preview"  # LLM model
embedding_model = "text-embedding-3-small"  # Embedding model
max_tokens = 2048  # Max response length
temperature = 0.3  # LLM temperature (0-1)
chunk_size = 1000  # Document chunk size
chunk_overlap = 200  # Overlap between chunks
top_k_results = 5  # Number of documents to retrieve
```

---

##  Advanced Usage

### Custom Guidelines

Add your own clinical documents:

```bash
# Add PDF, Markdown, or text files to:
data/guidelines/

# Re-index:
python scripts/index_documents.py
```

### Using Anthropic Claude

Set in `.env`:

```
ANTHROPIC_API_KEY=sk-ant-your-key
```

Update `backend/main.py`:

```python
rag_pipeline = RAGPipeline(provider="anthropic")
```

### Adjusting Retrieval

For more comprehensive retrieval:

```python
# In config/settings.py
top_k_results = 10  # Retrieve more documents
chunk_size = 500  # Smaller chunks for precision
```

---

##  Integration with Jupyter Notebook

### Export Patient from Notebook

```python
# In your sepsis prediction notebook:
import json

patient_data = {
    "patient_id": "PT-001",
    "vitals": {
        "heart_rate": float(hr_value),
        "systolic_bp": float(sbp_value),
        # ... other vitals
    },
    "labs": {
        "lactate": float(lactate_value),
        # ... other labs
    },
    "sofa_score": {
        "total": int(sofa_total),
        # ... SOFA components
    },
    "model_prediction": {
        "sepsis_probability": float(model.predict_proba(X)[0][1]),
        "risk_level": risk_tier,
        "confidence": float(confidence_score)
    }
}

with open('patient_export.json', 'w') as f:
    json.dump(patient_data, f, indent=2)
```

### Query from API

```python
import requests

response = requests.post(
    'http://localhost:8000/analyze_patient',
    json={'patient_context': patient_data}
)

analysis = response.json()
print(analysis['summary'])
print(analysis['recommendations'])
```

---

##  Performance Considerations

### Latency
- Document retrieval: ~100-200ms
- LLM generation: ~2-5 seconds
- Total response time: ~3-7 seconds

### Costs (OpenAI)
- Embedding (one-time indexing): ~$0.01 for 50 pages
- GPT-4 Turbo query: ~$0.03-0.10 per analysis
- Daily usage (20 queries): ~$0.60-2.00

### Optimization
- Cache embeddings (done automatically)
- Use GPT-3.5-turbo for lower cost
- Reduce `top_k_results` for faster retrieval

---

##  Safety & Limitations

###  Critical Warnings

1. **Not for Clinical Use**: This is an experimental educational tool
2. **Requires Validation**: All outputs must be verified by qualified clinicians
3. **Hallucination Risk**: LLMs can generate plausible but incorrect information
4. **No Liability**: Not approved or validated for patient care

### Known Limitations

- LLM knowledge cutoff (training data may be outdated)
- Potential for hallucinations or incorrect guidelines
- Limited to indexed documents
- No real-time critical alerts
- Requires internet connection for API calls

### Recommended Safeguards

1. Always cross-reference with primary sources
2. Use only as a supplementary reference tool
3. Maintain human oversight for all decisions
4. Log all interactions for review
5. Regular validation against current guidelines

---

##  Running Tests

```bash
pytest tests/ -v
```

---

##  Development Roadmap

### Future Enhancements

- [ ] Multi-modal input (imaging, waveforms)
- [ ] Real-time monitoring integration
- [ ] Custom fine-tuned models
- [ ] Audit logging and compliance tracking
- [ ] Multi-language support
- [ ] Mobile application
- [ ] Integration with EHR systems

---

##  Contributing

This is an educational project. Contributions welcome for:

- Additional clinical guidelines
- Improved prompt engineering
- Better evaluation metrics
- Documentation improvements

---

##  License

Educational use only. Not for clinical deployment.

---

##  Acknowledgments

- **Surviving Sepsis Campaign** for clinical guidelines
- **Anthropic** and **OpenAI** for LLM APIs
- **ChromaDB** for vector storage
- **LangChain** for RAG framework

---

##  Contact

For questions or feedback on this educational project, please open an issue.

---

##  Related Links

- [Surviving Sepsis Campaign](https://www.sccm.org/SurvivingSepsisCampaign)
- [SOFA Score Calculator](https://www.mdcalc.com/sofa-sequential-organ-failure-assessment-score)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [LangChain Documentation](https://python.langchain.com/)

---

**Remember: This tool is for educational purposes only. Always consult qualified healthcare professionals for patient care decisions.**
