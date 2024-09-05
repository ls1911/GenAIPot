# Copyright (C) 2024 Nucleon Cyber. All rights reserved.
#
# This file is part of GenAIPot.
#
# GenAIPot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or any later version.
#
# GenAIPot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GenAIPot. If not, see <http://www.gnu.org/licenses/>.
#
# For more information, visit: www.nucleon.sh or send email to contact[@]nucleon.sh
#

import logging
import argparse
import os
import sys
import configparser
from halo import Halo  # Halo spinner for feedback
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../src/ai'))

from ai.openai_service import OpenAIService
from ai.gcp_service import GCPService
from ai.azure_service import AzureAIService
from utils import save_raw_response

from twisted.internet import reactor
from smtp_protocol import SMTPFactory
from pop3.pop3_protocol import POP3Factory
from auth import check_credentials, hash_password
from database import setup_database
import art
import shutil

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
openai_key = config.get('openai', 'api_key', fallback=None)
gcp_project = config.get('gcp', 'project', fallback=None)
gcp_location = config.get('gcp', 'location', fallback=None)
gcp_model_id = config.get('gcp', 'model_id', fallback=None)
azure_openai_key = config.get('azure', 'api_key', fallback=None)
azure_openai_endpoint = config.get('azure', 'endpoint', fallback=None)

# Initialize AI service based on the provider chosen
spinner = Halo(text="Initializing AI Service", spinner='dots')
spinner.start()

try:
    if ai_provider == 'openai':
        if openai_key:
            ai_service = OpenAIService(api_key=openai_key, debug_mode=args.debug)
        else:
            logger.error("No OpenAI API key found in configuration.")
            sys.exit(1)
    elif ai_provider == 'gcp':
        if gcp_project and gcp_location and gcp_model_id:
            ai_service = GCPService(gcp_project=gcp_project, gcp_location=gcp_location, gcp_model_id=gcp_model_id, debug_mode=args.debug)
        else:
            logger.error("GCP configuration incomplete in config file.")
            sys.exit(1)
    elif ai_provider == 'azure':
        if azure_openai_key and azure_openai_endpoint:
            ai_service = AzureAIService(azure_openai_key=azure_openai_key, azure_openai_endpoint=azure_openai_endpoint, debug_mode=args.debug)
        else:
            logger.error("Azure OpenAI configuration incomplete in config file.")
            sys.exit(1)
    else:
        logger.error(f"Unsupported AI provider: {ai_provider}")
        sys.exit(1)
    spinner.succeed("AI Service initialized successfully.")
except Exception as e:
    spinner.fail(f"Failed to initialize AI service: {e}")
    sys.exit(1)

VERSION = "0.4.5"  # Incremented version number

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

def run_config_wizard():
    """Runs the configuration wizard to set up the honeypot."""
    if args.docker:
        print("Using Docker mode. Copying default configuration files without prompting.")
        config_src = os.path.join('var/no_ai', 'config.ini')
        config_dst = os.path.join('etc/', 'config.ini')
        if os.path.exists(config_src):
            shutil.copyfile(config_src, config_dst)
            print("Default configuration has been applied for Docker.")
        else:
            print(f"Config file not found at {config_src}")
        return

    # Ask the user to select the AI provider
    provider_choice = input("Choose the AI provider to use:\n"
                            "1. OpenAI\n"
                            "2. Azure OpenAI\n"
                            "3. Google Vertex AI\n"
                            "4. Offline (use pre-existing templates)\n"
                            "Enter the number of your choice: ")

    if provider_choice == '1':
        provider = 'openai'
        openai_key = input("Enter your OpenAI API key: ")
        if not config.has_section('openai'):
            config.add_section('openai')
        config.set('openai', 'api_key', openai_key)

    elif provider_choice == '2':
        provider = 'azure'
        azure_key = input("Enter your Azure OpenAI API key: ")
        azure_endpoint = input("Enter your Azure OpenAI endpoint: ")
        if not config.has_section('azure'):
            config.add_section('azure')
        config.set('azure', 'api_key', azure_key)
        config.set('azure', 'endpoint', azure_endpoint)

    elif provider_choice == '3':
        provider = 'gcp'
        gcp_key = input("Enter your Google Vertex AI API key: ")
        gcp_project = input("Enter your Google Project ID: ")
        gcp_location = input("Enter your Google Location: ")
        gcp_model_id = input("Enter your Google Model ID: ")
        if not config.has_section('gcp'):
            config.add_section('gcp')
        config.set('gcp', 'api_key', gcp_key)
        config.set('gcp', 'project', gcp_project)
        config.set('gcp', 'location', gcp_location)
        config.set('gcp', 'model_id', gcp_model_id)

    elif provider_choice == '4':
        provider = 'offline'
        print("Using offline mode with pre-existing configuration.")
    else:
        print("Invalid choice. Please run the configuration wizard again.")
        exit(1)

    # Ensure the 'ai' section exists before adding keys
    if not config.has_section('ai'):
        config.add_section('ai')

    # Set the chosen provider
    config.set('ai', 'provider', provider)

    # Ensure the 'server' section exists before adding configuration
    if not config.has_section('server'):
        config.add_section('server')

    # Configure honeypot with inputs
    technology = input("Choose the server technology to emulate:\n"
                       "1. sendmail\n"
                       "2. exchange\n"
                       "3. qmail\n"
                       "4. postfix\n"
                       "5. zimbra\n"
                       "6. other\n"
                       "Enter the number of your choice: ")
    technology = {'1': 'sendmail', '2': 'exchange', '3': 'qmail', '4': 'postfix', '5': 'zimbra', '6': 'other'}.get(technology, 'generic')
    
    segment = input("Enter the segment (industry description): ")
    domain = input("Enter the domain name (fictional company): ")
    anonymous_access = input("Allow anonymous access? (y/n): ").lower() == 'y'

    # Update the config file
    config.set('server', 'technology', technology)
    config.set('server', 'segment', segment)
    config.set('server', 'domain', domain)
    config.set('server', 'anonymous_access', str(anonymous_access))
    
    with Halo(text="Saving configuration...", spinner='dots') as spinner:
        try:
            with open(config_file_path, 'w') as configfile:
                config.write(configfile)
            spinner.succeed("Configuration has been saved.")
        except Exception as e:
            spinner.fail(f"Failed to save configuration: {e}")

    if provider != 'offline':
        query_ai_service_for_responses(technology, segment, domain, anonymous_access)

def query_ai_service_for_responses(technology, segment, domain, anonymous_access):
    """
    Query the AI service for SMTP and POP3 responses and sample emails.

    Args:
        technology (str): The technology used (e.g., sendmail, exchange).
        segment (str): The segment of the industry or application.
        domain (str): The domain name for the service.
        anonymous_access (bool): Whether anonymous access is allowed.
    """
    # Load prompts from prompts.ini
    prompts_config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'prompts.ini'))
    prompts = configparser.ConfigParser()
    prompts.read(prompts_config_file_path)

    smtp_prompt = prompts.get('Prompts', 'smtp_prompt').format(technology=technology)
    pop3_prompt = prompts.get('Prompts', 'pop3_prompt').format(technology=technology)
    email_prompts = [
        prompts.get('Prompts', 'client_email_prompt').format(segment=segment, domain=domain),
        prompts.get('Prompts', 'supplier_email_prompt').format(segment=segment, domain=domain),
        prompts.get('Prompts', 'internal_email_prompt').format(segment=segment, domain=domain)
    ]

    try:
        with Halo(text="SMTP Contacting A.I service and generating responses...", spinner='dots') as spinner:
            smtp_response = ai_service.query_responses(smtp_prompt, "smtp")
            save_raw_response(smtp_response, "smtp")
            spinner.succeed("SMTP responses generated successfully.")

        with Halo(text="POP3 Contacting A.I service and generating responses...", spinner='dots') as spinner:
            pop3_response = ai_service.query_responses(pop3_prompt, "pop3")
            save_raw_response(pop3_response, "pop3")
            spinner.succeed("POP3 responses generated successfully.")
        
        for idx, email_prompt in enumerate(email_prompts):
            with Halo(text=f"Generating sample email {idx+1}...", spinner='dots') as spinner:
                email_response = ai_service.query_responses(email_prompt, f"email_{idx+1}")
                save_raw_response(email_response, f"email_{idx+1}")
                spinner.succeed(f"Sample email {idx+1} generated successfully.")
    except Exception as e:
        print(f"Failed to generate responses: {e}")

def main():
    """Main function to run the GenAIPot honeypot services."""
    ensure_files_directory()

    # Set up the database
    setup_database()

    Art = art.text2art("GenAIPot")
    print(Art)
    print(f"Version: {VERSION}")
    print("The first Generative A.I Honeypot")

    if args.config or args.docker:
        run_config_wizard()
        return

    # Check which AI provider to use
    provider = config.get('ai', 'provider', fallback='offline')
    
    if provider == 'openai':
        api_key = config.get('openai', 'api_key', fallback=None)
        logging.debug(f"Retrieved OpenAI API key: {api_key}")  # Log the retrieved API key
        if api_key is None:
            logging.error("No OpenAI API key found in configuration.")
            return
        ai_service = OpenAIService(api_key=api_key, debug_mode=args.debug)
    elif provider == 'azure':
        api_key = config.get('azure', 'api_key', fallback=None)
        endpoint = config.get('azure', 'endpoint', fallback=None)
        if not api_key or not endpoint:
            logging.error("No Azure API key or endpoint found in configuration.")
            return
        ai_service = AzureAIService(azure_openai_key=api_key, azure_openai_endpoint=endpoint, debug_mode=args.debug)
    elif provider == 'gcp':
        api_key = config.get('gcp', 'api_key', fallback=None)
        project = config.get('gcp', 'project', fallback=None)
        location = config.get('gcp', 'location', fallback=None)
        model_id = config.get('gcp', 'model_id', fallback=None)
        if not api_key or not project or not location or not model_id:
            logging.error("GCP configuration incomplete in config file.")
            return
        ai_service = GCPService(gcp_project=project, gcp_location=location, gcp_model_id=model_id, debug_mode=args.debug)
    elif provider == 'offline':
        print("Using offline mode with pre-existing templates.")
        ai_service = None  # No AI service is used in offline mode
    else:
        print("Invalid AI provider specified in config. Exiting.")
        exit(1)

    if ai_service is not None:
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