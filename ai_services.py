import openai
import configparser
import logging
import json
import os
import time
from json_utils import extract_and_clean_json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

config = configparser.ConfigParser()
config.read('config.ini')

class AIService:
    """
    AIService class handles interactions with OpenAI's API, specifically for querying responses
    related to SMTP and POP3 protocols, and managing configuration settings.

    Attributes:
        technology (str): The technology type, default is 'generic'.
        domain (str): The domain name, default is 'localhost'.
        segment (str): The segment or category, default is 'general'.
        anonymous_access (bool): Flag indicating if anonymous access is allowed, default is False.
        debug_mode (bool): Flag indicating if debug mode is enabled.
    """

    def __init__(self, debug_mode=False):
        """
        Initializes the AIService class with configuration settings and sets up OpenAI API key.

        Args:
            debug_mode (bool): If True, enables debug logging. Default is False.
        """
        self.technology = config.get('server', 'technology', fallback='generic')
        self.domain = config.get('server', 'domain', fallback='localhost')
        self.segment = config.get('server', 'segment', fallback='general')
        self.anonymous_access = config.getboolean('server', 'anonymous_access', fallback=False)
        openai.api_key = config['openai']['api_key']
        self.debug_mode = debug_mode

        if self.debug_mode:
            logging.getLogger('openai').setLevel(logging.DEBUG)
            logging.getLogger('urllib3').setLevel(logging.DEBUG)
        else:
            logging.getLogger('openai').setLevel(logging.WARNING)
            logging.getLogger('urllib3').setLevel(logging.WARNING)

    def query_responses(self, prompt, response_type):
        """
        Queries the OpenAI API to get responses based on the provided prompt and response type.

        Args:
            prompt (str): The prompt to send to the OpenAI API.
            response_type (str): The type of response expected, e.g., 'smtp' or 'pop3'.

        Returns:
            str: The response text from the OpenAI API.
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
                logger.error(f"Error querying OpenAI (attempt {attempt+1}/2): {e}")
                if attempt == 1:
                    logger.error("Failed to communicate with AI after 2 attempts. Exiting.")
                    exit(1)
                time.sleep(1)

    def _save_raw_response(self, response_text, response_type):
        """
        Saves the raw response text from the AI model to a file.

        Args:
            response_text (str): The raw response text.
            response_type (str): The type of response, e.g., 'smtp' or 'pop3'.
        """
        filename = f'files/{self.technology}_{response_type}_raw_response.txt'
        with open(filename, 'w') as f:
            f.write(response_text)
        logger.info(f"Raw response saved in {filename}")

    def _store_responses(self, responses, response_type):
        """
        Stores the processed responses in a JSON file.

        Args:
            responses (dict): The responses to be stored.
            response_type (str): The type of responses, e.g., 'smtp' or 'pop3'.
        """
        filename = f'files/{self.technology}_{response_type}_responses.json'
        with open(filename, 'w') as f:
            json.dump(responses, f)
        logger.info(f"Responses stored in {filename}")

    def load_responses(self, response_type):
        """
        Loads responses from a file or provides default responses if the file does not exist.

        Args:
            response_type (str): The type of responses, e.g., 'smtp' or 'pop3'.

        Returns:
            dict: The loaded responses.
        """
        filename = f'files/{self.technology}_{response_type}_responses.json'
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return self.default_responses(response_type)

    def default_responses(self, response_type):
        """
        Provides default responses for SMTP and POP3 protocols.

        Args:
            response_type (str): The type of responses, e.g., 'smtp' or 'pop3'.

        Returns:
            dict: The default responses.
        """
        if response_type == "smtp":
            return {
                "220": f"{self.domain} {self.technology} SMTP server ready",
                "221": f"{self.domain} Service closing transmission channel",
                "250": "Requested mail action okay, completed",
                "251": "User not local; will forward",
                "354": "Start mail input; end with <CRLF>.<CRLF>",
                "421": "Service not available, closing transmission channel",
                "450": "Requested mail action not taken: mailbox unavailable",
                "451": "Requested action aborted: local error in processing",
                "452": "Requested action not taken: insufficient system storage",
                "500": "Syntax error, command unrecognized",
                "501": "Syntax error in parameters or arguments",
                "502": "Command not implemented",
                "503": "Bad sequence of commands",
                "504": "Command parameter not implemented",
                "550": "Requested action not taken: mailbox unavailable",
                "551": "User not local; please try",
                "552": "Requested mail action aborted: exceeded storage allocation",
                "553": "Requested action not taken: mailbox name not allowed",
                "554": "Transaction failed"
            }
        elif response_type == "pop3":
            return {
                "+OK": f"+OK {self.domain} {self.technology} POP3 server ready",
                "-ERR": "-ERR command not recognized"
            }

    def save_email_responses(self, email_response, email_num):
        """
        Saves email responses to a file.

        Args:
            email_response (dict): The email response data.
            email_num (int): The email number used for the filename.
        """
        filename = f'files/email_{email_num}.json'
        with open(filename, 'w') as f:
            json.dump(email_response, f)
        logger.info(f"Email {email_num} response stored in {filename}")

    def update_config_technology(self, technology):
        """
        Updates the configuration file with a new technology setting.

        Args:
            technology (str): The new technology setting.
        """
        config.set('server', 'technology', technology)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        logger.info(f"Config file updated with technology: {technology}")

    def update_config_segment(self, segment):
        """
        Updates the configuration file with a new segment setting.

        Args:
            segment (str): The new segment setting.
        """
        config.set('server', 'segment', segment)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        logger.info(f"Config file updated with segment: {segment}")

    def update_config_domain(self, domain):
        """
        Updates the configuration file with a new domain setting.

        Args:
            domain (str): The new domain setting.
        """
        config.set('server', 'domain', domain)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        logger.info(f"Config file updated with domain: {domain}")

    def update_config_anonymous_access(self, anonymous_access):
        """
        Updates the configuration file with the anonymous access setting.

        Args:
            anonymous_access (bool): The anonymous access setting.
        """
        config.set('server', 'anonymous_access', str(anonymous_access))
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        logger.info(f"Config file updated with anonymous access: {anonymous_access}")

    def cleanup_and_parse_json(self, text):
        """
        Cleans up and parses JSON from a given text.

        Args:
            text (str): The text containing JSON data.

        Returns:
            dict: The parsed JSON data or an empty dict if parsing fails.
        """
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start == -1 or end == 0:
                logger.error("Invalid JSON structure detected.")
                return {}

            json_text = text[start:end]
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.debug(f"Raw text for cleanup: {text}")
            cleaned_text = text[start:end].replace('\n', '').replace('\r', '')
            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing cleaned JSON: {e}")
                return {}

    def generate_emails(self, segment, domain, email_type):
        """
        Generates email content based on the specified segment, domain, and email type.

        Args:
            segment (str): The segment related to the email, e.g., 'marketing', 'sales'.
            domain (str): The domain name to be used in the email.
            email_type (str): The type of email to generate, e.g., 'welcome', 'newsletter'.

        Returns:
            dict: A dictionary containing the email's subject, body, sender, and recipient information.
        """
        try:
            prompt = (
                f"Generate an email for a {email_type} related to the segment: {segment} in JSON format. "
                f"The email should include a subject, body, mail from, and rcpt to field. The rcpt_to field "
                f"should include a random name and the domain {domain}."
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
            filename = f'files/{email_type}_raw_response.txt'
            with open(filename, 'w') as f:
                f.write(response_text)
            logger.info(f"Raw response saved in {filename}")

            email_json = self.cleanup_and_parse_json(response_text)
            return email_json
        except Exception as e:
            logger.error(f"Error querying OpenAI for {email_type} email: {e}")
            return {}