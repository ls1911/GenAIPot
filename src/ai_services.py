import openai
from ai.gcp_service import GCPService
from ai.openai_service import OpenAIService
from ai.azure_service import AzureAIService

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


def query_ai_service_for_responses(ai_service, prompts):
    """
    Query the AI service for SMTP and POP3 responses and sample emails.

    Args:
        ai_service (AIService): The initialized AIService object.
        prompts (dict): A dictionary containing different prompts for querying.

    Returns:
        dict: A dictionary containing AI service responses.
    """
    responses = {}

    try:
        smtp_response = ai_service.query_responses(prompts['smtp_prompt'], "smtp")
        responses['smtp'] = smtp_response
        print("✔ SMTP responses generated successfully.")
    except Exception as e:
        print(f"✘ Failed to generate SMTP responses: {e}")
    
    try:
        pop3_response = ai_service.query_responses(prompts['pop3_prompt'], "pop3")
        responses['pop3'] = pop3_response
        print("✔ POP3 responses generated successfully.")
    except Exception as e:
        print(f"✘ Failed to generate POP3 responses: {e}")

    for i, email_prompt in enumerate(prompts['email_prompts'], 1):
        try:
            email_response = ai_service.query_responses(email_prompt, f"email{i}")
            responses[f'email_{i}'] = email_response
            print(f"✔ Sample email {i} generated successfully.")
        except Exception as e:
            print(f"✘ Failed to generate sample email {i}: {e}")

    return responses