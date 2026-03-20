SEPSIS PREDICTION RAG SYSTEM v2.0

OVERVIEW
--------
LLM-powered clinical decision support system for sepsis prediction.
Integrates machine learning predictions with evidence-based clinical guidelines.

FEATURES
--------
- Patient analysis with AI-powered clinical reasoning
- Interactive chat interface for clinical questions
- RAG-based retrieval from Surviving Sepsis Campaign 2021 guidelines
- MIMIC data integration support
- Explainable AI with step-by-step reasoning chains

SYSTEM REQUIREMENTS
-------------------
- Python 3.9 or higher
- OpenAI API key
- 2GB free disk space
- Internet connection

INSTALLATION
------------

Step 1: Extract files
Extract sepsis_rag_v2_FINAL.zip to your desired location

Step 2: Navigate to directory
cd sepsis_rag_v2_FINAL

Step 3: Configure API key
cp .env.template .env
Edit .env file and add:
OPENAI_API_KEY=sk-your-actual-key-here

Step 4: Install dependencies
pip install -r requirements.txt

Step 5: Index clinical guidelines
python scripts/index_documents.py

Wait for completion message before proceeding.

Step 6: Start the system

Option A - Automated (Linux/Mac):
chmod +x start.sh
./start.sh

Option B - Manual:
Terminal 1:
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

Terminal 2:
streamlit run frontend/app.py

Step 7: Access the application
Open browser: http://localhost:8501

USAGE
-----

OPTION 1: DEMO MODE (NO JUPYTER NOTEBOOK REQUIRED)
1. Click "Load Demo Patient" in sidebar
2. Navigate to "Clinical Analysis" tab
3. Click "Generate Clinical Analysis"
4. View AI-generated assessment
5. Navigate to "Chat Assistant" tab
6. Ask questions about the patient

OPTION 2: MIMIC DATA INTEGRATION (REQUIRES JUPYTER NOTEBOOK)
1. Keep RAG system running
2. Open your Jupyter notebook with sepsis predictions
3. Add integration code (see MIMIC_INTEGRATION.md)
4. Export patient data to RAG system
5. Refresh browser and load your MIMIC patient

API ENDPOINTS
-------------
GET  /health           - System health check
GET  /stats            - Vector store statistics
POST /analyze_patient  - Generate patient analysis
POST /chat             - Interactive Q&A

Full API documentation: http://localhost:8000/docs

ARCHITECTURE
------------
Backend: FastAPI REST API
Frontend: Streamlit web interface
RAG Engine: ChromaDB + OpenAI GPT-4
Knowledge Base: Surviving Sepsis Campaign 2021 guidelines

FILE STRUCTURE
--------------
backend/           - FastAPI application
frontend/          - Streamlit UI
rag_engine/        - RAG pipeline components
models/            - Pydantic data schemas
config/            - Configuration management
scripts/           - Utility scripts
data/guidelines/   - Clinical guideline documents

MIMIC INTEGRATION
-----------------
See MIMIC_INTEGRATION.md for detailed instructions
See NOTEBOOK_SNIPPETS.py for ready-to-use code

COST ESTIMATES
--------------
Using OpenAI GPT-4 Turbo:
- Document indexing (one-time): $0.01
- Patient analysis: $0.06 each
- Chat message: $0.04 each
- 10 patients + 50 questions: approximately $3.00

TROUBLESHOOTING
---------------

Error: "OPENAI_API_KEY not set"
Solution: Edit .env file and add your API key

Error: "Module not found"
Solution: Run pip install -r requirements.txt

Error: "Backend connection failed"
Solution: Ensure backend is running on port 8000

Error: "No documents indexed"
Solution: Run python scripts/index_documents.py

Error: "Port already in use"
Solution: Change port in start.sh or kill existing process

FREQUENTLY ASKED QUESTIONS
--------------------------

Q: Do I need to run Jupyter notebook?
A: No. The system works standalone with demo patients.
   Only needed if you want to use your own MIMIC data.

Q: Where do I put my API key?
A: In the .env file in the project root directory.
   Copy .env.template to .env and add your key.

Q: Can I use Anthropic Claude instead of OpenAI?
A: Yes. Set ANTHROPIC_API_KEY in .env and modify
   backend/main.py line 23 to use provider="anthropic"

Q: How do I stop the system?
A: Press Ctrl+C in each terminal running the services

Q: Can I use this for real clinical decisions?
A: No. This is an experimental educational tool only.
   Not validated for clinical use.

DOCUMENTATION FILES
-------------------
README.md                  - This file
INSTALL.txt                - Installation guide
MIMIC_INTEGRATION.md       - MIMIC data integration
NOTEBOOK_SNIPPETS.py       - Code for Jupyter integration
PROJECT_ANALYSIS.md        - Technical deep-dive
ARCHITECTURE.md            - System design
QUICK_REFERENCE.md         - Command reference

DEMO WORKFLOW
-------------
1. Start system: ./start.sh
2. Open: http://localhost:8501
3. Click: "Load Demo Patient"
4. Click: "Generate Clinical Analysis"
5. Review: AI reasoning and recommendations
6. Navigate to: "Chat Assistant"
7. Ask: "Why is this patient high risk?"
8. Review: Answer with guideline citations

MIMIC WORKFLOW
--------------
1. Run your sepsis prediction model in Jupyter
2. Use mimic_integration.py to export patient
3. Patient appears in RAG system automatically
4. Load and analyze your real MIMIC patient
5. AI explains your model's predictions

INCLUDED GUIDELINES
-------------------
- Surviving Sepsis Campaign 2021 (complete)
- Initial resuscitation protocols
- Antimicrobial therapy timing
- Hemodynamic management
- Ventilation strategies  
- Long-term care recommendations

SUPPORT
-------
For issues or questions, refer to documentation files.
All code is provided as-is for educational purposes.

LICENSE
-------
Educational use only. Not for clinical deployment.

VERSION
-------
2.0.0 - Complete RAG implementation with MIMIC integration
