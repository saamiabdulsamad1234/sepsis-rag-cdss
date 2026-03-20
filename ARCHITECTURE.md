# System Architecture - Sepsis RAG v2.0

## High-Level Architecture

```

                         USER INTERFACE                           
                     (Streamlit Frontend)                         
               
   Overview    Analysis      Chat      Details         
               

                          HTTP/REST
                         ↓

                      FASTAPI BACKEND                             
                
     /health        /analyze          /chat               
                

                         
                         ↓

                      RAG PIPELINE                                
                                                                  
      
    1. Patient Context Builder                                
       • Parse vitals, labs, SOFA, predictions                
       • Create structured summary                            
      
                         ↓                                        
      
    2. Document Retrieval (Vector Store)                      
       • Query: patient context + question                    
       • Similarity search in ChromaDB                        
       • Retrieve top-K relevant chunks                       
      
                         ↓                                        
      
    3. Prompt Engineering                                     
       • Combine: summary + guidelines + question             
       • Apply clinical prompt template                       
       • Include conversation history                         
      
                         ↓                                        
      
    4. LLM Reasoning                                          
       • Send to GPT-4 / Claude                              
       • Generate clinical analysis                           
       • Extract reasoning steps                              
      
                         ↓                                        
      
    5. Response Processing                                    
       • Parse structured response                            
       • Map citations to sources                             
       • Calculate confidence                                 
       • Format for API response                              
      

                         
         
         ↓               ↓               ↓
    
  ChromaDB       OpenAI API     Clinical   
  Vector         GPT-4          Guidelines 
  Store          Embeddings     (PDF/MD)   
    
```

## Data Flow - Patient Analysis

```
1. User Loads Patient
   ↓
2. Frontend sends POST /analyze_patient
   {
     "patient_context": {
       "patient_id": "PT-HIGH-001",
       "vitals": {...},
       "labs": {...},
       "sofa_score": {...},
       "model_prediction": {...}
     }
   }
   ↓
3. Backend → RAGPipeline.analyze_patient()
   ↓
4. Create Patient Summary
   "Patient ID: PT-HIGH-001
    Age: 67, Male
    Heart Rate: 118 bpm
    MAP: 69 mmHg
    Lactate: 3.2 mmol/L
    SOFA: 8/24
    Sepsis Probability: 87%
    Risk: HIGH"
   ↓
5. Build Retrieval Query
   "sepsis risk assessment SOFA score HIGH"
   ↓
6. Vector Store Search
   • Embed query → 1536-dim vector
   • Cosine similarity with all chunks
   • Return top-5 matches
   ↓
7. Retrieved Documents
   [
     {source: "Surviving Sepsis 2021", score: 0.89, content: "..."},
     {source: "SOFA Criteria", score: 0.85, content: "..."},
     {source: "Lactate in Sepsis", score: 0.82, content: "..."},
     ...
   ]
   ↓
8. Build LLM Prompt
   "You are an expert clinical AI...
    
    PATIENT: [summary]
    
    GUIDELINES: [retrieved docs]
    
    TASK: Provide analysis with summary, findings, risks, 
          recommendations..."
   ↓
9. Call GPT-4
   • Temperature: 0.3
   • Max tokens: 2048
   • System: Clinical expert role
   ↓
10. LLM Response
    "CLINICAL ANALYSIS:
     This 67-year-old male presents with high sepsis risk...
     
     KEY FINDINGS:
     1. Tachycardia suggests compensatory response
     2. MAP 69 mmHg at critical threshold
     ...
     
     RECOMMENDATIONS:
     1. Immediate fluid resuscitation: 30 mL/kg
     2. Broad-spectrum antibiotics within 1 hour
     ..."
   ↓
11. Parse Response
    • Extract key_findings: [...]
    • Extract risk_factors: [...]
    • Extract recommendations: [...]
    • Extract reasoning_chain: [step1, step2, ...]
    • Determine urgency_level: "HIGH"
   ↓
12. Return Structured Response
    {
      "summary": "...",
      "key_findings": [...],
      "risk_factors": [...],
      "recommendations": [...],
      "urgency_level": "HIGH",
      "reasoning": "..."
    }
   ↓
13. Frontend Displays
    • Summary card
    • Findings bullets
    • Recommendations list
    • Expandable reasoning
```

## Data Flow - Interactive Chat

```
1. User Types Question
   "Why is lactate elevated?"
   ↓
2. Frontend sends POST /chat
   {
     "patient_context": {...},
     "question": "Why is lactate elevated?",
     "chat_history": [
       {role: "user", content: "..."},
       {role: "assistant", content: "..."}
     ]
   }
   ↓
3. Build Enhanced Query
   "Why is lactate elevated? HIGH risk patient with sepsis"
   ↓
4. Retrieve Relevant Docs
   Top-5 chunks about lactate and sepsis
   ↓
5. Build Conversational Prompt
   "PATIENT: [summary]
    
    GUIDELINES: [retrieved lactate info]
    
    PREVIOUS CONVERSATION:
    User: [previous question]
    Assistant: [previous answer]
    
    CURRENT QUESTION:
    Why is lactate elevated?
    
    INSTRUCTIONS:
    Provide evidence-based answer with reasoning..."
   ↓
6. Generate with History
   • Include full conversation context
   • Maintain coherence with previous answers
   ↓
7. LLM Response
   "Lactate is elevated in this patient due to tissue 
    hypoperfusion. When cells don't receive adequate oxygen,
    they switch to anaerobic metabolism, producing lactate...
    
    In this case, with MAP of 69 mmHg and SOFA cardiovascular
    score of 2, the elevated lactate (3.2 mmol/L) indicates...
    
    Per Sepsis-3 criteria, lactate >2 mmol/L combined with
    hypotension requiring vasopressors defines septic shock..."
   ↓
8. Extract Components
   • Answer text
   • Reasoning steps: [oxygen deprivation → anaerobic → lactate]
   • Citations: ["Sepsis-3 Criteria", "Lactate Physiology"]
   • Confidence: 0.88
   ↓
9. Return ChatResponse
   {
     "answer": "...",
     "retrieved_documents": [...],
     "reasoning_chain": [...],
     "confidence": 0.88,
     "citations": [...]
   }
   ↓
10. Frontend Updates
    • Append to chat history
    • Display answer
    • Show retrieved docs (expandable)
    • Show reasoning steps (expandable)
```

## Component Responsibilities

### Document Loader
```python
DocumentLoader:
   load_pdf()       # Extract text from PDFs
   load_markdown()  # Parse markdown files
   load_text()      # Read plain text
   load_directory() # Recursively load all files

Chunking Strategy:
  • RecursiveCharacterTextSplitter
  • Split on: \n\n → \n → . → (space)
  • Chunk size: 1000 tokens
  • Overlap: 200 tokens
```

### Vector Store Manager
```python
VectorStoreManager:
   add_documents()              # Index new documents
   similarity_search()          # Find similar chunks
   similarity_search_with_score() # With relevance scores
   get_collection_count()       # Stats

Technology:
  • ChromaDB (HNSW index)
  • OpenAI embeddings (text-embedding-3-small)
  • Persistent storage
  • Metadata filtering
```

### Reasoning Engine
```python
ReasoningEngine:
   generate_response()          # Single prompt
   generate_with_history()      # Conversational
   extract_reasoning_chain()    # Parse logic steps
   calculate_confidence()       # Estimate certainty

Providers:
  • OpenAI (GPT-4, GPT-3.5)
  • Anthropic (Claude 3)
  • Extensible for others
```

### Prompt Templates
```python
PromptTemplates:
   create_patient_summary()     # Structured data → text
   create_analysis_prompt()     # Full analysis request
   create_chat_prompt()         # Q&A with context
   format_retrieved_docs()      # Clean doc formatting

Design Principles:
  • Clear role definition
  • Structured context
  • Explicit instructions
  • Output format specification
```

### RAG Pipeline (Orchestrator)
```python
RAGPipeline:
   analyze_patient()    # Comprehensive analysis
   chat()              # Interactive Q&A
   get_store_stats()   # System metrics

Workflow:
  1. Parse input
  2. Retrieve documents
  3. Build prompt
  4. Generate response
  5. Process output
  6. Return structured result
```

## Technology Stack

### Backend
- **FastAPI**: REST API framework
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

### Frontend
- **Streamlit**: Interactive web UI
- **Requests**: HTTP client

### RAG Engine
- **LangChain**: RAG framework
- **ChromaDB**: Vector database
- **OpenAI**: LLM + embeddings
- **Anthropic**: Alternative LLM

### Document Processing
- **PyPDF**: PDF extraction
- **Markdown**: MD parsing
- **RecursiveCharacterTextSplitter**: Chunking

### Utilities
- **python-dotenv**: Environment config
- **tiktoken**: Token counting

## Deployment Architecture

```

              Load Balancer                  
           (nginx / AWS ALB)                 

              
      
      ↓                ↓
    
 Frontend      Frontend   (Streamlit)
 Instance      Instance 
    
                      
      
              ↓

           Backend API Cluster               
       
   FastAPI     FastAPI     FastAPI   
   Instance    Instance    Instance  
       

             
     
     ↓       ↓       ↓
  
ChromaDB  OpenAI    Redis    
Vector    API       Cache    
Store                        
  
```

## Security Architecture

```

         Authentication Layer                
  • API key validation                       
  • Role-based access control                
  • Session management                       

             ↓

         Authorization Layer                 
  • User permissions check                   
  • Resource access control                  
  • Audit logging                            

             ↓

         Encryption Layer                    
  • TLS for data in transit                 
  • Encryption for data at rest             
  • PHI protection (HIPAA)                  

             ↓

         Application Layer                   
  • Input validation                         
  • Output sanitization                      
  • Error handling                           

```

This architecture ensures:
-  Scalability (horizontal scaling)
-  Reliability (redundancy, failover)
-  Security (encryption, access control)
-  Performance (caching, load balancing)
-  Maintainability (modular, documented)
