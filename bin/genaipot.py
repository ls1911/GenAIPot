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
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from openai_service import OpenAIService
from gcp_service import GCPService
from azure_service import AzureAIService
from utils import save_raw_response
from twisted.internet import reactor
from smtp_protocol import SMTPFactory
from pop3.pop3_protocol import POP3Factory
from auth import check_credentials, hash_password
from database import setup_database
from halo import Halo
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

    openai_key = input("Enter your OpenAI API key: ")

    # Use spinner for key verification
    spinner = Halo(text='Verifying A.I key...', spinner='dots')
    spinner.start()
    if not validate_openai_key(openai_key):
        spinner.fail("Invalid API key provided.")
        use_default = input("Do you want to use default template files instead? (y/n): ").lower() == 'y'
        if use_default:
            # Copy default template files
            for filename in os.listdir('var/no_ai'):
                shutil.copyfile(os.path.join('var/no_ai', filename), os.path.join('files', filename))
            print("Default template files have been copied.")
        else:
            print("Exiting. Please provide a valid API key.")
            exit(1)
    spinner.succeed("API key validated.")

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
    config.set('ai', 'api_key', openai_key)
    config.set('server', 'technology', technology)
    config.set('server', 'segment', segment)
    config.set('server', 'domain', domain)
    config.set('server', 'anonymous_access', str(anonymous_access))
    
    with open(config_file_path, 'w') as configfile:
        config.write(configfile)
    print("Configuration has been saved.")

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
        smtp_response = ai_service.query_responses(smtp_prompt, "smtp")
        save_raw_response(smtp_response, "smtp")
        pop3_response = ai_service.query_responses(pop3_prompt, "pop3")
        save_raw_response(pop3_response, "pop3")
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

    # Check for the presence of an OpenAI API key or 'no_ai' setting
    api_key = config.get('ai', 'api_key', fallback='')
    
    if api_key == 'no_ai':
        print("Using default templates as no valid A.I key is set.")
    elif not validate_openai_key(api_key):
        print("No valid A.I key found. Please run the configuration wizard to set up the necessary key.")
        run_config_wizard()
        return

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