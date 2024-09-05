import openai
from ai.gcp_service import GCPService
from ai.openai_service import OpenAIService
from ai.azure_service import AzureAIService
import os
import configparser

class AIService:
    """
    AIService handles interactions with multiple AI services (OpenAI, GCP, Azure).
    """
    
    def __init__(self, api_key=None, service_type="openai", debug_mode=False):
        self.api_key = api_key
        self.service_type = service_type
        self.debug_mode = debug_mode
        
        # Initialize the appropriate service based on the type
        if service_type == "openai":
            self.service = OpenAIService(api_key, debug_mode)
        elif service_type == "gcp":
            self.service = GCPService(api_key, debug_mode)
        elif service_type == "azure":
            self.service = AzureAIService(api_key, debug_mode)
        else:
            raise ValueError(f"Unsupported service type: {service_type}")
    
    def query_responses(self, prompt, response_type):
        """
        Query the selected AI service based on the initialized service type.

        Args:
            prompt (str): The prompt to send to the AI service.
            response_type (str): The expected response type (e.g., "email").
        
        Returns:
            str: The response from the AI service.
        """
        return self.service.query_responses(prompt, response_type)
    
    def validate_key(self):
        """
        Validate the API key for the selected AI service.
        """
        return self.service.validate_key()


def validate_openai_key(api_key):
    """
    Validate the OpenAI API key by making a simple API call.
    If valid, returns True; otherwise, raises an error.

    Args:
        api_key (str): The OpenAI API key.
    
    Returns:
        bool: True if the API key is valid, False otherwise.
    """
    if not api_key:
        raise ValueError("OpenAI API key is missing.")
    
    try:
        openai.api_key = api_key
        # Validate by calling a simple API (e.g., listing available engines)
        openai.Engine.list()
        print("✔ API key validated.")
        return True
    except Exception as e:
        print(f"✘ Invalid OpenAI API key: {e}")
        return False


def query_ai_service_for_responses(technology, segment):
    """
    Query the AI service for SMTP and POP3 responses and sample emails.

    Args:
        technology (str): The technology used (e.g., sendmail, exchange).
        segment (str): The segment of the industry or application.
    """
    # Load prompts from prompts.ini
    prompts_config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'prompts.ini'))
    prompts = configparser.ConfigParser()
    prompts.read(prompts_config_file_path)

    smtp_prompt = prompts.get('Prompts', 'smtp_prompt').format(technology=technology)
    pop3_prompt = prompts.get('Prompts', 'pop3_prompt').format(technology=technology)

    email_prompts = [
        prompts.get('Prompts', 'client_email_prompt').format(segment=segment),
        prompts.get('Prompts', 'supplier_email_prompt').format(segment=segment),
        prompts.get('Prompts', 'internal_email_prompt').format(segment=segment)
    ]

    try:
        smtp_response = ai_service.query_responses(smtp_prompt, "smtp")
        save_raw_response(smtp_response, "smtp")
        print("✔ SMTP responses generated successfully.")
    except Exception as e:
        print(f"✘ Failed to generate SMTP responses: {e}")

    try:
        pop3_response = ai_service.query_responses(pop3_prompt, "pop3")
        save_raw_response(pop3_response, "pop3")
        print("✔ POP3 responses generated successfully.")
    except Exception as e:
        print(f"✘ Failed to generate POP3 responses: {e}")

    for i, email_prompt in enumerate(email_prompts, 1):
        try:
            email_response = ai_service.query_responses(email_prompt, f"email_{i}")
            save_raw_response(email_response, f"email_{i}")
            print(f"✔ Sample email {i} generated successfully.")
        except Exception as e:
            print(f"✘ Failed to generate email {i}: {e}")