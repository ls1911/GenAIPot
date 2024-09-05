import requests
import logging
from utils import save_raw_response

class AzureAIService:
    def __init__(self, azure_openai_key=None, azure_openai_endpoint=None, debug_mode=False):
        self.azure_openai_key = azure_openai_key
        self.azure_openai_endpoint = azure_openai_endpoint
        self.debug_mode = debug_mode

    def query_azure_openai(self, prompt, response_type):
        headers = {
            "Content-Type": "application/json",
            "api-key": self.azure_openai_key
        }
        data = {
            "prompt": prompt,
            "max_tokens": 500
        }
        try:
            response = requests.post(
                f"{self.azure_openai_endpoint}/openai/deployments/your-deployment-id/completions?api-version=2022-12-01",
                headers=headers,
                json=data
            )
            response_text = response.json()["choices"][0]["text"].strip()
            save_raw_response(response_text, response_type)
            return response_text
        except Exception as e:
            if self.debug_mode:
                logging.error(f"Error querying Azure OpenAI: {e}")
            return ""