import os
import vertexai
from typing import Optional

try:
    from vertexai.generative_models import GenerativeModel, Tool, GoogleSearchRetrieval
except ImportError:
    # Fallback for some versions or different import paths
    from vertexai.generative_models import GenerativeModel, Tool
    try:
        from vertexai.generative_models import GoogleSearchRetrieval
    except ImportError:
        GoogleSearchRetrieval = None

class VertexRAGService:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.data_store_id = os.getenv("VERTEX_DATA_STORE_ID")
        
        if self.project_id:
            vertexai.init(project=self.project_id, location=self.location)
            # Initialize Gemini 1.5 Flash for speed
            self.model = GenerativeModel("gemini-1.5-flash")
        else:
            print("Warning: GOOGLE_CLOUD_PROJECT not set. VertexRAGService will run in mock mode.")
            self.model = None

    async def query(self, text: str) -> str:
        """
        Queries Gemini with Grounding from Vertex AI Search.
        """
        if not self.model:
            return f"Réponse simulée pour : {text}. (Veuillez configurer GOOGLE_CLOUD_PROJECT)"

        try:
            # Use Vertex AI Search grounding if data_store_id is set
            tools = []
            if GoogleSearchRetrieval:
                tools.append(
                    Tool.from_google_search_retrieval(
                        google_search_retrieval=GoogleSearchRetrieval()
                    )
                )
            
            response = self.model.generate_content(
                f"Contexte: Tu es un assistant vocal utile et poli. Réponds en français de manière concise et naturelle. Garde tes réponses brèves pour une conversation vocale.\nUtilisateur: {text}",
                tools=tools
            )
            return response.text
        except Exception as e:
            print(f"Error querying Vertex AI: {e}")
            return "Désolé, j'ai des difficultés à me connecter à ma base de connaissances pour le moment."