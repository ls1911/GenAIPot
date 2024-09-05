import logging
from openai_service import OpenAIService
from gcp_service import GCPService
from azure_service import AzureAIService

class AIService:
    def __init__(self, openai_key=None, gcp_project=None, gcp_location=None, gcp_model_id=None,
                 azure_openai_key=None, azure_openai_endpoint=None, debug_mode=False):
        self.openai_service = OpenAIService(openai_key, debug_mode)
        self.gcp_service = GCPService(gcp_project, gcp_location, gcp_model_id, debug_mode)
        self.azure_service = AzureAIService(azure_openai_key, azure_openai_endpoint, debug_mode)
        self.debug_mode = debug_mode

    def query_responses(self, prompt, response_type, use_openai=True, use_azure_openai=False):
        if use_azure_openai:
            return self.azure_service.query_azure_openai(prompt, response_type)
        elif use_openai:
            return self.openai_service.query_openai(prompt, response_type)
        else:
            return self.gcp_service.query_gcp_gemini(prompt, response_type)