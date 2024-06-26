import openai
from azure.ai.openai import OpenAIClient
from azure.core.credentials import AzureKeyCredential
from google.cloud import aiplatform
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

class AIService:
    def __init__(self, use_azure=False, use_gcp=False):
        self.use_azure = use_azure
        self.use_gcp = use_gcp

        if self.use_azure:
            self.azure_client = OpenAIClient(
                config['azure']['endpoint'],
                AzureKeyCredential(config['azure']['api_key'])
            )
            self.azure_deployment_name = config['azure']['deployment_name']
        elif self.use_gcp:
            aiplatform.init(project=config['gcp']['project_id'])
            self.gcp_model = aiplatform.Model(config['gcp']['model_name'])
        else:
            openai.api_key = config['openai']['api_key']

    def generate_response(self, command):
        prompt = (
            f"Generate a realistic and variable POP3 response for the command: {command}. "
            "The response should adhere to the POP3 RFC standards."
        )

        if self.use_azure:
            response = self.azure_client.completions.create(
                engine=self.azure_deployment_name,
                prompt=prompt,
                max_tokens=50
            )
            return response.choices[0].text.strip()
        elif self.use_gcp:
            response = self.gcp_model.predict([prompt])
            return response[0]
        else:
            response = openai.Completion.create(
                engine="davinci",
                prompt=prompt,
                max_tokens=50
            )
            return response.choices[0].text.strip()