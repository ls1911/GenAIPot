import openai
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
from google.protobuf import json_format
import os
import configparser
import logging
import time
import json
from halo import Halo
import requests

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)  # Default to ERROR level

# Load the config.ini file
config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'config.ini'))
config = configparser.ConfigParser()
config.read(config_file_path)

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
        return True
    except Exception as e:
        err=(f"Invalid OpenAI API key: {e}")        
        return False

class AIService:
    """
    AIService handles interactions with multiple AI services (OpenAI, GCP, and Azure).

    Attributes:
        technology (str): The technology field from the config.
        domain (str): The domain field from the config.
        segment (str): The segment field from the config.
        anonymous_access (bool): The anonymous access field from the config.
        debug_mode (bool): Flag for enabling debug mode.
        gcp_project (str): GCP project ID for Gemini API Vertex.
        gcp_location (str): GCP location for Gemini API Vertex.
        gcp_model_id (str): Model ID for Gemini API Vertex.
        azure_endpoint (str): Azure OpenAI endpoint.
        azure_location (str): Azure OpenAI location/region.
    """

    def __init__(self, api_key=False, gcp_project=None, gcp_location=None, gcp_model_id=None, azure_endpoint=None, azure_location=None, debug_mode=False):
        """
        Initialize AIService with API key for OpenAI, Azure, and GCP project details.

        Args:
            api_key (str): The API key for OpenAI or Azure.
            gcp_project (str): GCP project ID for Google AI.
            gcp_location (str): GCP location for Google AI.
            gcp_model_id (str): Model ID for Google AI.
            azure_endpoint (str): The Azure OpenAI API endpoint.
            azure_location (str): The Azure OpenAI API location/region.
            debug_mode (bool): If True, enables debug logging.
        """
        self.technology = config.get('server', 'technology', fallback='generic')
        self.domain = config.get('server', 'domain', fallback='localhost')
        self.segment = config.get('server', 'segment', fallback='general')
        self.anonymous_access = config.getboolean('server', 'anonymous_access', fallback=False)

        openai.api_key = api_key  # Set the API key directly
        
        self.gcp_project = gcp_project
        self.gcp_location = gcp_location
        self.gcp_model_id = gcp_model_id
        self.azure_endpoint = azure_endpoint  # New attribute for Azure OpenAI
        self.azure_location = azure_location  # New attribute for Azure location
        self.debug_mode = debug_mode

        if self.debug_mode:
            logging.getLogger('ai_services').setLevel(logging.DEBUG)
            logging.getLogger('urllib3').setLevel(logging.DEBUG)
        else:
            logging.getLogger('ai_services').setLevel(logging.CRITICAL)
            logging.getLogger('urllib3').setLevel(logging.CRITICAL)
    
    def query_responses(self, prompt, response_type, use_openai=True):
        """
        Query AI services (OpenAI or Google Gemini Vertex) for responses based on the provided prompt and response type.

        Args:
            prompt (str): The prompt to send to the AI service.
            response_type (str): The type of response expected (e.g., "email").
            use_openai (bool): Whether to use OpenAI (True) or Gemini Vertex (False).

        Returns:
            str: The response text from the AI service.
        """
        if use_openai:
            return self._query_openai(prompt, response_type)
        else:
            return self._query_gcp_gemini(prompt, response_type)

    def _query_openai(self, prompt, response_type):
        """
        Query OpenAI's API for a response to the provided prompt.

        Args:
            prompt (str): The prompt to send to OpenAI.
            response_type (str): The type of response expected (e.g., "email").

        Returns:
            str: The response text from OpenAI, or an empty string if there was an error.
        """
        for attempt in range(2):
            try:
                if self.debug_mode:
                    logger.debug(f"Querying OpenAI for {response_type} responses...")
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500
                )
                response_text = response.choices[0]['message']['content'].strip()
                self._save_raw_response(response_text, response_type)
                return response_text
            except Exception as e:
                if self.debug_mode:
                    logger.error(f"Error querying OpenAI (attempt {attempt+1}/2): {e}")
                if attempt == 1:
                    logger.critical("Failed to communicate with AI after 2 attempts. Exiting.")
                time.sleep(1)
        return ""

    def _query_gcp_gemini(self, prompt, response_type):
        """
        Query Google's Gemini API Vertex for a response to the provided prompt.

        Args:
            prompt (str): The prompt to send to Google Gemini API.
            response_type (str): The type of response expected (e.g., "email").

        Returns:
            str: The response text from Google Gemini Vertex, or an empty string if there was an error.
        """
        try:
            if self.debug_mode:
                logger.debug(f"Querying Google Gemini Vertex for {response_type} responses...")
            
            client = aiplatform.gapic.PredictionServiceClient()
            endpoint = f"projects/{self.gcp_project}/locations/{self.gcp_location}/endpoints/{self.gcp_model_id}"

            instances = [{"content": prompt}]
            parameters = {}
            request = predict.instance.PredictRequest(
                endpoint=endpoint,
                instances=[json_format.ParseDict(instances, predict.instance.Value())],
                parameters=json_format.ParseDict(parameters, predict.instance.Value()),
            )
            response = client.predict(request=request)
            response_text = response.predictions[0].get("content", "").strip()
            self._save_raw_response(response_text, response_type)
            return response_text
        except Exception as e:
            if self.debug_mode:
                logger.error(f"Error querying Google Gemini Vertex: {e}")
            return ""

    def _save_raw_response(self, response_text, response_type):
        """
        Save the raw response text to a file.

        Args:
            response_text (str): The response text from the AI service.
            response_type (str): The type of response (e.g., "email").
        """
        filename = f'files/{response_type}_raw_response.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response_text)
        if self.debug_mode:
            logger.debug(f"Raw response saved in {filename}")

    def _store_responses(self, responses, response_type):
        """
        Store the parsed responses in a JSON file.

        Args:
            responses (dict): The parsed responses.
            response_type (str): The type of response (e.g., "email").
        """
        filename = f'files/{response_type}_responses.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(responses, f)
        if self.debug_mode:
            logger.debug(f"Responses stored in {filename}")

    def load_responses(self, response_type):
        """
        Load responses from a saved file.

        Args:
            response_type (str): The type of response (e.g., "email").

        Returns:
            str: The loaded response text.
        """
        filename = f'files/{response_type}_raw_response.txt'
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        return "No responses available"

    def cleanup_and_parse_json(self, text):
        """
        Clean up and parse a JSON string from text.

        Args:
            text (str): The text containing JSON.

        Returns:
            dict: The parsed JSON object, or an empty dict if parsing fails.
        """
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start == -1 or end == 0:
                if self.debug_mode:
                    logger.error("Invalid JSON structure detected.")
                    logger.debug(f"Raw text: {text}")
                return {}

            json_text = text[start:end]
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            if self.debug_mode:
                logger.error(f"Error parsing JSON response: {e}")
                logger.debug(f"Raw text for cleanup: {text}")
            return {}

    def generate_emails(self, segment, domain, email_num):
        """
        Generate a sample email related to the given segment and domain.

        This method uses the OpenAI API to generate a sample email, including
        the subject, body, and recipient address. The email content is saved
        to a file for later use.

        Args:
            segment (str): The segment or topic of the email.
            domain (str): The domain to use for the email address.
            email_num (int): The identifier number for the email.

        Returns:
            str: The generated email content.
        """
        try:
            prompt = (
                f"Generate an email related to the segment: {segment} for the domain {domain}. "
                f"The email should include a subject, body, and a recipient address at the domain."
            )
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            response_text = response.choices[0]['message']['content'].strip()

            # Save the raw response to a file
            filename = f'files/email{email_num}_raw_response.txt'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response_text)
            if self.debug_mode:
                logger.debug(f"Raw response saved in {filename}")

            return response_text
        except Exception as e:
            if self.debug_mode:
                logger.error(f"Error querying OpenAI for email {email_num}: {e}")
            return "No response"

import logging

def query_ai_service_for_responses(technology, segment, domain, anonymous_access, debug_mode, ai_service):
    """
    Query the AI service for SMTP and POP3 responses and sample emails.

    Args:
        technology (str): The technology used (e.g., sendmail, exchange).
        segment (str): The segment of the industry or application.
        domain (str): The domain name for the service.
        anonymous_access (bool): Whether anonymous access is allowed.
        debug_mode (bool): Whether to enable debug mode.
        ai_service (AIService): The AI service to query (OpenAI, GCP, Azure).
    """

    # Load prompts from prompts.ini configuration file
    prompts_config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'prompts.ini'))
    
    # Initialize configparser to read prompts
    prompts = configparser.ConfigParser()
    prompts.read(prompts_config_file_path)

    # Check if the prompts configuration file has been loaded correctly
    if not prompts.sections():
        raise FileNotFoundError(f"Prompts configuration file not found at {prompts_config_file_path}")

    # Load prompts for the responses
    smtp_prompt = prompts.get('Prompts', 'smtp_prompt').format(technology=technology)
    pop3_prompt = prompts.get('Prompts', 'pop3_prompt').format(technology=technology)
    email_prompts = [
        prompts.get('Prompts', 'client_email_prompt').format(segment=segment, domain=domain),
        prompts.get('Prompts', 'supplier_email_prompt').format(segment=segment, domain=domain),
        prompts.get('Prompts', 'internal_email_prompt').format(segment=segment, domain=domain)
    ]

    # Function to log or print the data if debug mode is enabled
    def log_debug_info(request_type, prompt, response):
        if debug_mode:
            logging.debug(f"Request ({request_type}): {prompt}")
            logging.debug(f"Response ({request_type}): {response}")

    # Try to get SMTP responses
    try:
        #if debug_mode:
        spinner = Halo(text='Generating SMTP responses with AI service.. (1/5)')
        spinner.start()  # Start the spinner while processing
        smtp_raw_response = ai_service.query_responses(smtp_prompt, "smtp")
        log_debug_info("SMTP", smtp_prompt, smtp_raw_response)  # Log or print the SMTP request and response
        smtp_cleaned_response = ai_service.cleanup_and_parse_json(smtp_raw_response)
        ai_service._store_responses(smtp_cleaned_response, "smtp")
        spinner.succeed("SMTP responses generated successfully.")
    except Exception as e:
        spinner.fail(f"Failed to communicate with AI for SMTP responses: {e}")
        return

    # Try to get POP3 responses
    try:
            spinner = Halo(text='Generating POP3 responses with AI service.. (2/5)', spinner='dots')    
            spinner.start()  # Start the spinner while processing
            pop3_raw_response = ai_service.query_responses(pop3_prompt, "pop3")
            log_debug_info("POP3", pop3_prompt, pop3_raw_response)  # Log the POP3 request and response

            # Cleanup and parse the response
            pop3_cleaned_response = ai_service.cleanup_and_parse_json(pop3_raw_response)

            # Store the parsed response
            ai_service._store_responses(pop3_cleaned_response, "pop3")

            spinner.succeed("POP3 responses generated successfully.")  # Show success
    except Exception as e:
            spinner.fail(f"Failed to communicate with AI for POP3 responses: {e}")  # Show failure
            return

    # Try to get email responses
    for i, email_prompt in enumerate(email_prompts, 1):
        try:
            o=i+2
            spinner = Halo(text=f"Sending email prompt #{i} to AI service.. ({o}/5)", spinner='dots')    
            spinner.start()
#            if debug_mode:
                #logging.debug(f"Sending email prompt #{i} to AI service...")
            email_raw_response = ai_service.query_responses(email_prompt, f"email_{i}")
            log_debug_info(f"Email {i}", email_prompt, email_raw_response)  # Log or print the email request and response
            email_cleaned_response = ai_service.cleanup_and_parse_json(email_raw_response)
            #ai_service.save_email_responses(email_cleaned_response, f"email_{i}")
            spinner.succeed(f"Sample email #{i} generated successfully.")
        except Exception as e:
            spinner.fail(f"Failed to communicate with AI for email #{i}: {e}")

def validate_azure_key(api_key, endpoint, location):
    """
    Validate the Azure OpenAI API key by making a simple API call.
    If valid, returns True; otherwise, returns False.

    Args:
        api_key (str): The Azure OpenAI API key.
        endpoint (str): The Azure OpenAI endpoint.
        location (str): The Azure OpenAI location/region.

    Returns:
        bool: True if the API key is valid, False otherwise.
    """
    headers = {
        'api-key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Form the URL for the API call, using the provided endpoint
    url = f"{endpoint}/openai/deployments?api-version=2023-05-15"

    try:
        # Send a GET request to validate the key and endpoint
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            print("✔ API key is valid.")
            return True
        else:
            print(f"✘ API key validation failed. Status Code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✘ An error occurred while validating the API key: {e}")
        return False