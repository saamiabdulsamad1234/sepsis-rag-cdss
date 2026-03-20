# Quick Reference Guide - Sepsis RAG v2.0

##  30-Second Start

```bash
cd sepsis_rag_v2
cp .env.template .env
# Add your OPENAI_API_KEY to .env
./start.sh
```

Visit: http://localhost:8501

---

##  Common Commands

### Setup
```bash
pip install -r requirements.txt
python scripts/index_documents.py
python scripts/create_test_patients.py
```

### Start Services
```bash
# Backend
cd backend && uvicorn main:app --reload --port 8000

# Frontend (new terminal)
streamlit run frontend/app.py
```

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Analyze patient
curl -X POST http://localhost:8000/analyze_patient \
  -H "Content-Type: application/json" \
  -d @data/test_patients/PT-HIGH-001.json
```

---

##  Key Features

### 1. Patient Analysis
- Load demo patient → Clinical Analysis tab → Generate Analysis
- View: Summary, Findings, Risks, Recommendations, Reasoning

### 2. Interactive Chat
- Chat Assistant tab → Ask questions about the patient
- Examples:
  - "Why is lactate elevated?"
  - "What antibiotics should I start?"
  - "Explain the SOFA score"

### 3. View Retrieved Guidelines
- Expand "Retrieved Guidelines" in chat responses
- See sources and relevance scores

### 4. Reasoning Chain
- Expand "Reasoning Steps" to see LLM logic
- Understand how conclusions were reached

---

##  Configuration

### .env File
```
OPENAI_API_KEY=sk-your-key-here
MODEL_NAME=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small
TEMPERATURE=0.3
TOP_K_RESULTS=5
```

### Switch to Anthropic Claude
```
ANTHROPIC_API_KEY=sk-ant-your-key
```

In `backend/main.py`:
```python
rag_pipeline = RAGPipeline(provider="anthropic")
```

---

##  Demo Patients

### PT-HIGH-001 (High Risk Sepsis)
- 67M, HR 118, MAP 69, Lactate 3.2
- SOFA 8/24, 87% sepsis probability
- Suspected pneumonia

### PT-MODERATE-002 (Moderate Risk)
- 54F, HR 105, MAP 81, Lactate 2.1
- SOFA 3/24, 58% sepsis probability
- UTI symptoms

### PT-CRITICAL-003 (Septic Shock)
- 72M, HR 135, MAP 56, Lactate 5.8
- SOFA 14/24, 96% sepsis probability
- Septic shock, suspected perforation

---

##  Troubleshooting

### Backend won't start
```bash
# Check Python version
python3 --version  # Need 3.9+

# Check dependencies
pip install -r requirements.txt

# Check API key
grep OPENAI_API_KEY .env
```

### Documents not indexed
```bash
python scripts/index_documents.py

# Verify
curl http://localhost:8000/stats
```

### Frontend connection error
```bash
# Ensure backend is running
curl http://localhost:8000/health

# Check port 8000 not in use
lsof -i :8000
```

### Empty responses from LLM
- Check API key is valid
- Check API credits/quota
- Check network connection
- Review backend logs for errors

---

##  API Endpoints

### GET /health
Check system status
```json
{
  "status": "healthy",
  "vector_store": "connected",
  "documents_loaded": 25
}
```

### GET /stats
Get vector store statistics
```json
{
  "total_documents": 25,
  "collection_name": "sepsis_guidelines"
}
```

### POST /analyze_patient
Analyze a patient
```json
{
  "patient_context": { ... }
}
```

Response:
```json
{
  "summary": "...",
  "key_findings": [...],
  "risk_factors": [...],
  "recommendations": [...],
  "urgency_level": "HIGH",
  "reasoning": "..."
}
```

### POST /chat
Interactive Q&A
```json
{
  "patient_context": { ... },
  "question": "Why is this patient high risk?",
  "chat_history": []
}
```

Response:
```json
{
  "answer": "...",
  "retrieved_documents": [...],
  "reasoning_chain": [...],
  "confidence": 0.85,
  "citations": [...]
}
```

---

##  For Professors/Reviewers

### What to Look At

1. **RAG Architecture** (`rag_engine/pipeline.py`)
   - Document retrieval logic
   - Prompt construction
   - Response processing

2. **LLM Reasoning** (`rag_engine/reasoning.py`)
   - Multi-step reasoning extraction
   - Confidence calibration
   - Provider abstraction

3. **Clinical Prompts** (`rag_engine/prompts.py`)
   - Medical domain adaptation
   - Structured output formatting
   - Context management

4. **API Design** (`backend/main.py`)
   - RESTful endpoints
   - Error handling
   - Data validation

5. **Test the System**
   - Load PT-HIGH-001
   - Generate analysis
   - Ask follow-up questions
   - Review reasoning chains

### Key Innovations

-  Semantic chunking with overlap
-  Hybrid query construction (patient + question)
-  Multi-step reasoning extraction
-  Citation mapping to sources
-  Confidence calibration
-  Production-ready architecture

### Academic Value

- Novel RAG application in medical domain
- Addresses explainability in healthcare AI
- Demonstrates clinical knowledge grounding
- Replicable methodology
- Clear evaluation framework

---

##  Performance

### Latency
- Document retrieval: ~100-200ms
- LLM generation: ~2-5s
- Total: ~3-7s per query

### Costs (OpenAI GPT-4)
- Per analysis: $0.06
- Per chat message: $0.04
- 100 patients/day: ~$10/day

### Optimization
- Use GPT-3.5 for cost: 10x cheaper
- Cache common queries
- Reduce top_k_results for speed

---

##  Safety Notes

 **NOT FOR CLINICAL USE**
- Educational/research tool only
- Requires clinical validation
- LLM hallucination risk
- Always verify with authoritative sources

---

##  Support

### Documentation
- Full README: `README.md`
- Technical analysis: `PROJECT_ANALYSIS.md`
- Code documentation: Inline docstrings

### API Docs
Visit: http://localhost:8000/docs (when backend running)

### Example Usage
See: `data/test_patients/*.json`

---

**Last Updated**: 2024  
**Version**: 2.0  
**License**: Educational Use Only
