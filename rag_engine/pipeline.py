from typing import List, Dict, Tuple
from models.schemas import (
    PatientContext, ChatRequest, ChatResponse, 
    AnalysisRequest, AnalysisResponse, RetrievedDocument
)
from rag_engine.vector_store import VectorStoreManager
from rag_engine.reasoning import ReasoningEngine
from rag_engine.prompts import PromptTemplates
from config.settings import settings

class RAGPipeline:
    def __init__(self, provider: str = "openai"):
        self.vector_store = VectorStoreManager()
        self.reasoning_engine = ReasoningEngine(provider=provider)
        self.prompt_templates = PromptTemplates()
    
    def _retrieve_relevant_docs(
        self, 
        query: str, 
        k: int = None
    ) -> Tuple[List[RetrievedDocument], str]:
        k = k or settings.top_k_results
        
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        retrieved_docs = []
        for doc, score in results:
            retrieved_docs.append(RetrievedDocument(
                content=doc.page_content,
                source=doc.metadata.get('source', 'Unknown'),
                relevance_score=float(score),
                metadata=doc.metadata
            ))
        
        formatted_docs = self.prompt_templates.format_retrieved_docs(
            [doc for doc, _ in results]
        )
        
        return retrieved_docs, formatted_docs
    
    def analyze_patient(self, request: AnalysisRequest) -> AnalysisResponse:
        patient_summary = self.prompt_templates.create_patient_summary(
            request.patient_context
        )
        
        query = f"sepsis risk assessment SOFA score {request.patient_context.model_prediction.risk_level.value}"
        retrieved_docs, formatted_docs = self._retrieve_relevant_docs(query)
        
        analysis_prompt = self.prompt_templates.create_analysis_prompt(
            patient_summary, 
            formatted_docs
        )
        
        response = self.reasoning_engine.generate_response(analysis_prompt)
        
        reasoning_chain = self.reasoning_engine.extract_reasoning_chain(response)
        
        key_findings = []
        risk_factors = []
        recommendations = []
        urgency_level = "MODERATE"
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'key finding' in line.lower() or 'concerning' in line.lower():
                current_section = 'findings'
            elif 'risk factor' in line.lower():
                current_section = 'risks'
            elif 'recommendation' in line.lower():
                current_section = 'recommendations'
            elif line.startswith('-') or line.startswith('•') or line.startswith(tuple('123456789')):
                if current_section == 'findings':
                    key_findings.append(line.lstrip('-•0123456789. '))
                elif current_section == 'risks':
                    risk_factors.append(line.lstrip('-•0123456789. '))
                elif current_section == 'recommendations':
                    recommendations.append(line.lstrip('-•0123456789. '))
        
        if request.patient_context.model_prediction.risk_level.value == "HIGH":
            urgency_level = "HIGH"
        elif request.patient_context.model_prediction.risk_level.value == "CRITICAL":
            urgency_level = "CRITICAL"
        elif request.patient_context.sofa_score.total >= 10:
            urgency_level = "HIGH"
        
        if not key_findings:
            key_findings = [
                f"SOFA score: {request.patient_context.sofa_score.total}/24",
                f"Sepsis probability: {request.patient_context.model_prediction.sepsis_probability:.1%}",
                f"Risk level: {request.patient_context.model_prediction.risk_level.value}"
            ]
        
        if not recommendations:
            recommendations = [
                "Continuous vital signs monitoring",
                "Repeat laboratory assessments",
                "Consider escalation of care if deterioration"
            ]
        
        return AnalysisResponse(
            summary=response[:500] + "..." if len(response) > 500 else response,
            key_findings=key_findings[:5],
            risk_factors=risk_factors[:5],
            recommendations=recommendations[:5],
            urgency_level=urgency_level,
            reasoning="\n".join(reasoning_chain)
        )
    
    def chat(self, request: ChatRequest) -> ChatResponse:
        patient_summary = self.prompt_templates.create_patient_summary(
            request.patient_context
        )
        
        query = f"{request.question} {request.patient_context.model_prediction.risk_level.value}"
        retrieved_docs, formatted_docs = self._retrieve_relevant_docs(query)
        
        chat_history_dict = [
            {"role": msg.role, "content": msg.content} 
            for msg in request.chat_history
        ]
        
        chat_prompt = self.prompt_templates.create_chat_prompt(
            patient_summary,
            formatted_docs,
            request.question,
            chat_history_dict
        )
        
        if request.chat_history:
            response = self.reasoning_engine.generate_with_history(
                chat_prompt,
                request.chat_history
            )
        else:
            response = self.reasoning_engine.generate_response(chat_prompt)
        
        reasoning_chain = self.reasoning_engine.extract_reasoning_chain(response)
        
        confidence = self.reasoning_engine.calculate_confidence(response)
        
        citations = list(set([doc.source for doc in retrieved_docs]))
        
        return ChatResponse(
            answer=response,
            retrieved_documents=retrieved_docs,
            reasoning_chain=reasoning_chain,
            confidence=confidence,
            citations=citations
        )
    
    def get_store_stats(self) -> Dict:
        return {
            "total_documents": self.vector_store.get_collection_count(),
            "collection_name": self.vector_store.collection_name
        }
