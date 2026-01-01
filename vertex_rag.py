import os
import vertexai
from typing import Optional
import google.generativeai as genai

try:
    from vertexai.generative_models import GenerativeModel, Tool, GoogleSearchRetrieval
except ImportError:
    from vertexai.generative_models import GenerativeModel, Tool
    GoogleSearchRetrieval = None

class VertexRAGService:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.data_store_id = os.getenv("VERTEX_DATA_STORE_ID")
        self.api_key = os.getenv("GOOGLE_API_KEY") # For Google AI Fallback
        
        self.use_vertex = False
        if self.project_id and not self.project_id.startswith("gen-lang-client"):
            try:
                vertexai.init(project=self.project_id, location=self.location)
                self.model = GenerativeModel("gemini-1.5-flash-002")
                self.use_vertex = True
                print(f"Using Vertex AI with project {self.project_id}")
            except Exception as e:
                print(f"Failed to init Vertex AI: {e}")
                self.model = None
        else:
            self.model = None

        # Fallback to Google AI (AI Studio) if Vertex is not available or project looks like AI Studio
        if not self.use_vertex:
            if self.api_key:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                print("Using Google AI Studio SDK (Fallback)")
            else:
                print("Warning: Neither Vertex AI nor Google AI API Key set.")

    def query(self, text: str, history: list = None) -> str:
        if not self.model:
            return f"Service IA non configuré. (Reçu : {text})"

        try:
            context_prompt = "Tu es un assistant vocal utile et poli. Réponds en français de manière concise."
            history_text = ""
            if history:
                history_text = "\nHistorique:\n" + "\n".join(history)
            
            full_prompt = f"{context_prompt}{history_text}\nUtilisateur: {text}"

            # Tools only work on Vertex AI generally in this SDK
            tools = []
            if self.use_vertex and GoogleSearchRetrieval:
                tools.append(Tool.from_google_search_retrieval(GoogleSearchRetrieval()))
            
            if self.use_vertex:
                response = self.model.generate_content(full_prompt, tools=tools)
            else:
                response = self.model.generate_content(full_prompt)
                
            return response.text
        except Exception as e:
            print(f"Error querying AI: {e}")
            return "Désolé, j'ai rencontré une erreur technique en consultant mon intelligence."