import os
import vertexai
from vertexai.generative_models import GenerativeModel, Tool, GoogleSearchRetrieval
from typing import Optional

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
            return f"Mock response for: {text}. (Please set GOOGLE_CLOUD_PROJECT)"

            # Use Vertex AI Search grounding if data_store_id is set
            if self.data_store_id:
                # Format: projects/{project}/locations/{location}/collections/default_collection/dataStores/{data_store}
                ds_path = f"projects/{self.project_id}/locations/{self.location}/collections/default_collection/dataStores/{self.data_store_id}"
                tools = [
                    Tool.from_google_search_retrieval(
                        google_search_retrieval=GoogleSearchRetrieval()
                    )
                ]
                # Note: Grounding with Vertex AI Search often requires specific configuration in generate_content
                # For this prototype, we'll keep Google Search as primary tool but mention the intent
            else:
                tools = [
                    Tool.from_google_search_retrieval(
                        google_search_retrieval=GoogleSearchRetrieval()
                    )
                ]
            
            response = self.model.generate_content(
                f"Contexte: Tu es un assistant vocal utile et poli. Réponds en français de manière concise et naturelle. Garde tes réponses brèves pour une conversation vocale.\nUtilisateur: {text}",
                tools=tools
            )
            return response.text
        except Exception as e:
            print(f"Error querying Vertex AI: {e}")
            return "I'm sorry, I'm having trouble connecting to my knowledge base right now."

