from typing import List, Dict, Tuple, Optional
import json
from openai import OpenAI
from anthropic import Anthropic
from config.settings import settings
from models.schemas import ChatMessage

class ReasoningEngine:
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        
        if provider == "openai":
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = settings.model_name
        elif provider == "anthropic":
            self.client = Anthropic(api_key=settings.anthropic_api_key)
            self.model = "claude-3-sonnet-20240229"
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def generate_response(
        self, 
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        max_tokens = max_tokens or settings.max_tokens
        temperature = temperature or settings.temperature
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert clinical decision support AI specializing in sepsis management and critical care."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                return response.content[0].text
        
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"Error: Unable to generate response. {str(e)}"
    
    def generate_with_history(
        self,
        prompt: str,
        chat_history: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        max_tokens = max_tokens or settings.max_tokens
        temperature = temperature or settings.temperature
        
        try:
            if self.provider == "openai":
                messages = [
                    {
                        "role": "system",
                        "content": "You are an expert clinical decision support AI specializing in sepsis management and critical care."
                    }
                ]
                
                for msg in chat_history:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
                
                messages.append({
                    "role": "user",
                    "content": prompt
                })
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                formatted_messages = []
                for msg in chat_history:
                    formatted_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
                
                formatted_messages.append({
                    "role": "user",
                    "content": prompt
                })
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=formatted_messages
                )
                return response.content[0].text
        
        except Exception as e:
            print(f"Error generating response with history: {e}")
            return f"Error: Unable to generate response. {str(e)}"
    
    def extract_json_from_response(self, response: str) -> Optional[Dict]:
        try:
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            
            return None
        
        except Exception as e:
            print(f"Error extracting JSON: {e}")
            return None
    
    def extract_reasoning_chain(self, response: str) -> List[str]:
        reasoning_steps = []
        
        lines = response.split('\n')
        current_step = ""
        
        for line in lines:
            line = line.strip()
            if any(line.startswith(f"{i}.") for i in range(1, 20)):
                if current_step:
                    reasoning_steps.append(current_step.strip())
                current_step = line
            elif line.startswith('-') or line.startswith('•'):
                if current_step:
                    current_step += " " + line[1:].strip()
            elif current_step and line:
                current_step += " " + line
        
        if current_step:
            reasoning_steps.append(current_step.strip())
        
        if not reasoning_steps:
            paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
            reasoning_steps = paragraphs[:5]
        
        return reasoning_steps
    
    def calculate_confidence(self, response: str) -> float:
        confidence_keywords = {
            'definitely': 0.95,
            'clearly': 0.9,
            'highly likely': 0.85,
            'strongly suggests': 0.8,
            'indicates': 0.75,
            'suggests': 0.7,
            'possibly': 0.5,
            'uncertain': 0.3,
            'unclear': 0.3
        }
        
        response_lower = response.lower()
        confidence = 0.7
        
        for keyword, score in confidence_keywords.items():
            if keyword in response_lower:
                confidence = max(confidence, score)
                break
        
        return confidence
