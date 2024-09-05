import logging
import argparse
import os
import sys
import configparser

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))  # Adjusted path

from ai.openai_service import OpenAIService  # Adjusted for src/ai directory
from ai.gcp_service import GCPService  # Adjusted for src/ai directory
from ai.azure_service import AzureAIService  # Adjusted for src/ai directory
from utils import save_raw_response
from twisted.internet import reactor
from smtp_protocol import SMTPFactory
from pop3.pop3_protocol import POP3Factory
from auth import check_credentials, hash_password
from database import setup_database
from halo import Halo
import art
import shutil

from config_wizard import run_config_wizard  # Import the function from the external config_wizard.py file

# Initialize argument parser
parser = argparse.ArgumentParser(description="GenAIPot - A honeypot simulation tool")
parser.add_argument('--config', action='store_true', help='Configure the honeypot with AI-generated responses')
parser.add_argument('--docker', action='store_true', help='Use default config for Docker deployment')
parser.add_argument('--smtp', action='store_true', help='Start SMTP honeypot')
parser.add_argument('--pop3', action='store_true', help='Start POP3 honeypot')
parser.add_argument('--all', action='store_true', help='Start all honeypots')
parser.add_argument('--debug', action='store_true', help='Enable debug mode')
args = parser.parse_args()

# Set up logging based on the debug flag
if args.debug:
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

# Read config file to determine which AI provider to use
config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'config.ini'))
config = configparser.ConfigParser()
config.read(config_file_path)

ai_provider = config.get('ai', 'provider', fallback='openai')  # 'openai', 'gcp', or 'azure'
api_key = config.get('ai', 'api_key', fallback=None)
gcp_project = config.get('gcp', 'project', fallback=None)
gcp_location = config.get('gcp', 'location', fallback=None)
gcp_model_id = config.get('gcp', 'model_id', fallback=None)
azure_openai_key = config.get('azure', 'api_key', fallback=None)
azure_openai_endpoint = config.get('azure', 'endpoint', fallback=None)

# Initialize AI service based on the provider chosen
if ai_provider == 'openai':
    ai_service = OpenAIService(api_key=api_key, debug_mode=args.debug)
elif ai_provider == 'gcp':
    ai_service = GCPService(gcp_project=gcp_project, gcp_location=gcp_location, gcp_model_id=gcp_model_id, debug_mode=args.debug)
elif ai_provider == 'azure':
    ai_service = AzureAIService(azure_openai_key=azure_openai_key, azure_openai_endpoint=azure_openai_endpoint, debug_mode=args.debug)
else:
    raise ValueError(f"Unsupported AI provider: {ai_provider}")

VERSION = "0.6.1"  # Updated version number

def ensure_files_directory():
    """Ensure the existence of the 'files' directory."""
    if not os.path.exists('files'):
        os.makedirs('files')

def validate_openai_key(api_key):
    """Validate the OpenAI API key by making a simple API call."""
    try:
        ai_service.validate_key()  # Moved the validation to the service class
        print("API key is valid.")
        return True
    except Exception as e:
        print(f"API key validation failed: {e}")
        return False

def main():
    """Main function to run the GenAIPot honeypot services."""
    ensure_files_directory()

    # Set up the database
    setup_database()

    Art = art.text2art("GenAIPot")
    print(Art)
    print(f"Version: {VERSION}")
    print("The first Generative A.I Honeypot")

    # If --config or --docker is specified, run the configuration wizard
    if args.config or args.docker:
        run_config_wizard(args, config, config_file_path)
        
        # Re-read the config after configuration
        config.read(config_file_path)

    # Check which AI provider to use
    provider = config.get('ai', 'provider', fallback='offline')

    if provider == 'openai':
        api_key = config.get('openai', 'api_key', fallback=None)
        logging.debug(f"Retrieved OpenAI API key: {api_key}")  # Log the retrieved API key
        if not api_key:
            logging.error("No OpenAI API key found in configuration.")
        else:
            ai_service = OpenAIService(api_key=api_key, debug_mode=args.debug)
    elif provider == 'azure':
        api_key = config.get('azure', 'api_key', fallback=None)
        endpoint = config.get('azure', 'endpoint', fallback=None)
        ai_service = AzureAIService(azure_openai_key=api_key, azure_openai_endpoint=endpoint, debug_mode=args.debug)
    elif provider == 'gcp':
        api_key = config.get('gcp', 'api_key', fallback=None)
        project = config.get('gcp', 'project', fallback=None)
        location = config.get('gcp', 'location', fallback=None)
        model_id = config.get('gcp', 'model_id', fallback=None)
        ai_service = GCPService(gcp_project=project, gcp_location=location, gcp_model_id=model_id, debug_mode=args.debug)
    elif provider == 'offline':
        print("Using offline mode with pre-existing templates.")
        ai_service = None  # No AI service is used in offline mode
    else:
        print("Invalid AI provider specified in config. Exiting.")
        exit(1)

    if ai_service and provider != 'offline':
        validate_openai_key(api_key)

    if args.smtp or args.pop3 or args.all:
        try:
            print("\n")
            logger.info(f"Starting GenAIPot Version {VERSION}")
            if args.debug:
                start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Start Time: {start_time}")
                logger.info(f"IP: {config.get('server', 'ip', fallback='localhost')}")
                logger.info(f"Listening Ports: {', '.join(['25', '110']) if args.all else ('25' if args.smtp else '110')}")
                logger.info(f"SQLite Logging Enabled: {config.getboolean('logging', 'sqlite', fallback=True)}")
                logger.info(f"Server Technology: {config.get('server', 'technology', fallback='generic')}")
                logger.info(f"Domain Name: {config.get('server', 'domain', fallback='localhost')}")
                logging.getLogger('urllib3').setLevel(logging.DEBUG)

            if args.smtp or args.all:
                smtp_factory = SMTPFactory()
                reactor.listenTCP(25, smtp_factory)
                logger.info("SMTP honeypot started on port 25")

            if args.pop3 or args.all:
                pop3_factory = POP3Factory(debug=args.debug)
                reactor.listenTCP(110, pop3_factory)
                logger.info("POP3 honeypot started on port 110")

            logger.info("Reactor is running...")
            reactor.run()
        except Exception as e:
            logger.error(f"Failed to start honeypot: {e}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()