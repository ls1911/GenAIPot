#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 Nucleon Cyber. All rights reserved.
#
# This file is part of GenAIPot.
#
# GenAIPot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
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
import datetime
import shutil
from twisted.internet import reactor
from halo import Halo
import art

# Adjust sys.path to include 'src' directory if necessary
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai.openai_service import OpenAIService  # Adjusted for src/ai directory
from ai.gcp_service import GCPService  # Adjusted for src/ai directory
from ai.azure_service import AzureAIService  # Adjusted for src/ai directory
from smtp_protocol import SMTPFactory
from pop3.pop3_protocol import POP3Factory
from auth import check_credentials, hash_password
from database import setup_database
from config_wizard import run_config_wizard  # Import the function from the external config_wizard.py file

VERSION = "0.6.6"

def ensure_files_directory():
    """Ensure the existence of the 'files' directory."""
    if not os.path.exists('files'):
        os.makedirs('files')

def initialize_logging(debug_mode):
    """
    Initialize logging configuration.

    Args:
        debug_mode (bool): Whether to enable debug mode.

    Returns:
        logger: Configured logger instance.
    """
    log_level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    return logger

def read_configuration():
    """
    Read the configuration files.

    Returns:
        tuple: A tuple containing the main config, prompts config, and config file path.
    """
    config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'config.ini'))
    config = configparser.ConfigParser()
    config.read(config_file_path)

    prompts_config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'prompts.ini'))
    prompts = configparser.ConfigParser()
    prompts.read(prompts_config_file_path)

    return config, prompts, config_file_path

def initialize_ai_service(config, args):
    """Initialize the AI service based on the provider from the configuration."""
    ai_provider = config.get('ai', 'provider', fallback='offline')  # 'openai', 'gcp', 'azure', or 'offline'

    if ai_provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY') or config.get('openai', 'api_key', fallback=None)
        if not api_key:
            logging.error("No OpenAI API key found in environment variables or configuration.")
            return None
        return OpenAIService(api_key=api_key, debug_mode=args.debug)

    elif ai_provider == 'azure':
        api_key = os.getenv('AZURE_API_KEY') or config.get('azure', 'api_key', fallback=None)
        endpoint = config.get('azure', 'endpoint', fallback=None)
        if not api_key or not endpoint:
            logging.error("No Azure API key or endpoint found in environment variables or configuration.")
            return None
        return AzureAIService(azure_openai_key=api_key, azure_openai_endpoint=endpoint, debug_mode=args.debug)

    elif ai_provider == 'gcp':
        # Handle GCP credentials as needed
        api_key = os.getenv('GCP_API_KEY') or config.get('gcp', 'api_key', fallback=None)
        project = config.get('gcp', 'project', fallback=None)
        location = config.get('gcp', 'location', fallback=None)
        model_id = config.get('gcp', 'model_id', fallback=None)
        if not api_key or not project or not location or not model_id:
            logging.error("Incomplete GCP configuration.")
            return None
        return GCPService(gcp_project=project, gcp_location=location, gcp_model_id=model_id, debug_mode=args.debug)

    elif ai_provider == 'offline':
        print("Using offline mode with pre-existing templates.")
        return None  # No AI service is used in offline mode

    else:
        print("Invalid AI provider specified in config. Exiting.")
        sys.exit(1)

def query_ai_service_for_responses(config, prompts, ai_service, debug_mode):
    """
    Query the AI service for SMTP and POP3 responses and sample emails.

    Args:
        config (ConfigParser): The configuration object.
        prompts (ConfigParser): The prompts configuration object.
        ai_service (object): The initialized AI service instance.
        debug_mode (bool): Whether to enable debug mode.
    """
    technology = config.get('server', 'technology', fallback='generic')
    segment = config.get('server', 'segment', fallback='general')
    domain = config.get('server', 'domain', fallback='localhost')
    anonymous_access = config.getboolean('server', 'anonymous_access', fallback=False)

    # Prepare prompts
    smtp_prompt = prompts.get('Prompts', 'smtp_prompt').format(technology=technology)
    pop3_prompt = prompts.get('Prompts', 'pop3_prompt').format(technology=technology)
    email_prompts = [
        prompts.get('Prompts', 'client_email_prompt').format(segment=segment, domain=domain),
        prompts.get('Prompts', 'supplier_email_prompt').format(segment=segment, domain=domain),
        prompts.get('Prompts', 'internal_email_prompt').format(segment=segment, domain=domain)
    ]

    # Query SMTP responses
    generate_responses(ai_service, smtp_prompt, 'smtp', 'SMTP', debug_mode)

    # Query POP3 responses
    generate_responses(ai_service, pop3_prompt, 'pop3', 'POP3', debug_mode)

    # Query sample emails
    for idx, email_prompt in enumerate(email_prompts, start=1):
        response_type = f'email_{idx}'
        description = f'Sample Email #{idx}'
        spinner = Halo(text=f'{description}: Generating responses...', spinner='dots')
        spinner.start()
        try:
            response_text = ai_service.query_responses(email_prompt, response_type)
            cleaned_response = ai_service.cleanup_and_parse_json(response_text)
            ai_service.save_email_responses(cleaned_response, response_type)
            spinner.succeed(f'{description} generated successfully.')
        except Exception as e:
            spinner.fail(f'Failed to generate {description}.')
            if debug_mode:
                logging.exception(f"Error generating {description}: {e}")

def generate_responses(ai_service, prompt, response_type, description, debug_mode):
    """
    Helper function to query AI service and handle responses.

    Args:
        ai_service (object): The initialized AI service instance.
        prompt (str): The prompt to send to the AI service.
        response_type (str): The type of response (e.g., 'smtp', 'pop3').
        description (str): A description for logging and display purposes.
        debug_mode (bool): Whether to enable debug mode.
    """
    spinner = Halo(text=f'{description}: Generating responses...', spinner='dots')
    spinner.start()
    try:
        response_text = ai_service.query_responses(prompt, response_type)
        cleaned_response = ai_service.cleanup_and_parse_json(response_text)
        ai_service.store_responses(cleaned_response, response_type)
        spinner.succeed(f'{description} responses generated successfully.')
    except Exception as e:
        spinner.fail(f'Failed to generate {description} responses.')
        if debug_mode:
            logging.exception(f"Error generating {description} responses: {e}")

def main():
    """
    Main function to run the GenAIPot honeypot services.
    """
    # Initialize argument parser
    parser = argparse.ArgumentParser(description="GenAIPot - A honeypot simulation tool")
    parser.add_argument('--config', action='store_true', help='Configure the honeypot with AI-generated responses')
    parser.add_argument('--docker', action='store_true', help='Use default config for Docker deployment')
    parser.add_argument('--smtp', action='store_true', help='Start SMTP honeypot')
    parser.add_argument('--pop3', action='store_true', help='Start POP3 honeypot')
    parser.add_argument('--all', action='store_true', help='Start all honeypots')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    # Initialize logging
    logger = initialize_logging(args.debug)

    # Always print logo and version information
    art_text = art.text2art("Gen.A.I.Pot")
    print(art_text)
    print(f"Version: {VERSION}")
    print("The first Generative A.I Honeypot")

    # If no arguments are provided, show the help menu
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    ensure_files_directory()

    # Read configuration
    config, prompts, config_file_path = read_configuration()

    # Set up the database
    setup_database()

    # If --config or --docker is specified, run the configuration wizard
    if args.config or args.docker:
        run_config_wizard(args, config, config_file_path)
        # Re-read the config after configuration
        config.read(config_file_path)
        # No need to proceed further after configuration
        return

    # Initialize the AI service
    ai_service = initialize_ai_service(config, args)

    # If AI service is initialized, and 'offline' mode is not selected, generate responses
    if ai_service and (args.config or args.docker):
        # Generate AI responses if necessary
        query_ai_service_for_responses(config, prompts, ai_service, args.debug)

    # If SMTP, POP3, or both services are selected, start them
    if args.smtp or args.pop3 or args.all:
        try:
            logger.info(f"Starting GenAIPot Version {VERSION}")

            if args.debug:
                start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.debug(f"Start Time: {start_time}")
                logger.debug(f"IP: {config.get('server', 'ip', fallback='localhost')}")
                listening_ports = ', '.join(['25', '110']) if args.all else ('25' if args.smtp else '110')
                logger.debug(f"Listening Ports: {listening_ports}")
                logger.debug(f"SQLite Logging Enabled: {config.getboolean('logging', 'sqlite', fallback=True)}")
                logger.debug(f"Server Technology: {config.get('server', 'technology', fallback='generic')}")
                logger.debug(f"Domain Name: {config.get('server', 'domain', fallback='localhost')}")
                logging.getLogger('urllib3').setLevel(logging.DEBUG)

            # Start SMTP service
            if args.smtp or args.all:
                smtp_factory = SMTPFactory()
                reactor.listenTCP(25, smtp_factory)
                logger.info("SMTP honeypot started on port 25")

            # Start POP3 service
            if args.pop3 or args.all:
                pop3_factory = POP3Factory(debug=args.debug)
                reactor.listenTCP(110, pop3_factory)
                logger.info("POP3 honeypot started on port 110")

            logger.info("Reactor is running...")
            reactor.run()

        except Exception as e:
            logger.exception(f"Failed to start honeypot: {e}")
    else:
        # If no specific honeypot service is selected, show the help menu
        parser.print_help()

if __name__ == "__main__":
    main()