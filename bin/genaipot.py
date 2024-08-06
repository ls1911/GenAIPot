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
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import configparser
import datetime
from twisted.internet import reactor
from smtp_protocol import SMTPFactory
from pop3.pop3_protocol import POP3Factory
from ai_services import AIService
from auth import check_credentials, hash_password
from database import setup_database
from halo import Halo
import openai
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

# Read config file
prompts_config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'prompts.ini'))
config_config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'config.ini'))

config = configparser.ConfigParser()
config.read(config_config_file_path)
prompts = configparser.ConfigParser()

prompts.read(prompts_config_file_path)

VERSION = "0.4.4"  # Incremented version number

def ensure_files_directory():
    """Ensure the existence of the 'files' directory."""
    if not os.path.exists('files'):
        os.makedirs('files')

def validate_openai_key(api_key):
    """Validate the OpenAI API key by making a simple API call."""
    openai.api_key = api_key
    try:
        # Attempt a simple API request to verify the key
        openai.Engine.list()

        spinner = Halo(text="API key is valid.", spinner='dots')
        spinner.start()
        spinner.stop_and_persist(symbol='🦄'.encode('utf-8'))
        print("---------------------------------------")
        return True
    except openai.error.AuthenticationError:
        print("Invalid API key. Please enter a valid OpenAI API key.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
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

    spinner = Halo(text="Initiating Configuration Wizard", spinner='dots')
    spinner.start()
    spinner.stop_and_persist(symbol='🦄'.encode('utf-8'))

    openai_key = input("Enter your OpenAI API key: ")

    # Use Halo spinner for key verification
    with Halo(text='Verifying A.I key...', spinner='dots') as spinner:
        if not validate_openai_key(openai_key):
            spinner.fail("A valid key is needed for GenAIPot to function properly.")
            use_default = input("Do you want to use default template files instead of the A.I service generating them dynamically for you? (y/n): ").lower() == 'y'
            if not use_default:
                print("Exiting the application. Please provide a valid OpenAI API key.")
                exit(1)
            else:
                # Copy default files from var/no_ai to files/
                if not os.path.exists('files'):
                    os.makedirs('files')
                for filename in os.listdir('var/no_ai'):
                    src_path = os.path.join('var/no_ai', filename)
                    dst_path = os.path.join('files', filename)
                    shutil.copyfile(src_path, dst_path)
                    if not os.path.exists(src_path):
                        print(f"Source directory does not exist: {src_path}")

                config_dst = os.path.join('etc/', 'config.ini')
                config_src = os.path.join('var/no_ai', 'config.ini')
                if os.path.exists(config_src):
                    shutil.copyfile(config_src, config_dst)
                    print("Default template files have been used.")
                else:
                    print(f"Config file not found at {config_src}")

                return

        spinner.succeed("A.I key verified successfully.")

    technology = input("Choose the server technology to emulate:\n"
                       "1. sendmail\n"
                       "2. exchange\n"
                       "3. qmail\n"
                       "4. postfix\n"
                       "5. zimbra\n"
                       "6. other\n"
                       "Enter the number of your choice: ")
    technology = {
        '1': 'sendmail',
        '2': 'exchange',
        '3': 'qmail',
        '4': 'postfix',
        '5': 'zimbra',
        '6': 'other'
    }.get(technology, 'generic')

    segment = input("Enter the segment (Description of the industry segment; for example: an international bank located in nome alsaka.): ")
    domain = input("Enter the domain name (name for your fictional company): ")
    anonymous_access = input("Allow anonymous access? (y/n): (if yes, any username will be accepted)").lower() == 'y'

    if not anonymous_access:
        username = input("Enter username: ")
        password = input("Enter password: ")
        hashed_password = hash_password(password)
        config.set('server', 'username', username)
        config.set('server', 'password', hashed_password)
    else:
        if config.has_option('server', 'username'):
            config.remove_option('server', 'username')
        if config.has_option('server', 'password'):
            config.remove_option('server', 'password')

    with Halo(text='Saving configuration...', spinner='dots') as spinner:
        # Save the configuration to the config file
        if not config.has_section('openai'):
            config.add_section('openai')
        if not config.has_section('server'):
            config.add_section('server')

        config.set('openai', 'api_key', openai_key)
        config.set('server', 'technology', technology)
        config.set('server', 'segment', segment)
        config.set('server', 'domain', domain)
        config.set('server', 'anonymous_access', str(anonymous_access))

        with open('etc/config.ini', 'w') as configfile:
            config.write(configfile)

        spinner.succeed("Configuration has been saved successfully.")


    print("Configuration has been saved.")

    # Generate responses and sample emails using the AI service
    query_ai_service_for_responses(technology, segment, domain, anonymous_access, args.debug,openai_key)

def query_ai_service_for_responses(technology, segment, domain, anonymous_access, debug_mode,api_key):
    """
    Query the AI service for SMTP and POP3 responses and sample emails.

    Args:
        technology (str): The technology used (e.g., sendmail, exchange).
        segment (str): The segment of the industry or application.
        domain (str): The domain name for the service.
        anonymous_access (bool): Whether anonymous access is allowed.
        debug_mode (bool): Whether to enable debug mode.
    """
    ai_service = AIService(api_key=api_key, debug_mode=debug_mode)

    # Load prompts from prompts.ini
    smtp_prompt = prompts.get('Prompts', 'smtp_prompt').format(technology=technology)
    pop3_prompt = prompts.get('Prompts', 'pop3_prompt').format(technology=technology)
    email_prompts = [
        prompts.get('Prompts', 'client_email_prompt').format(segment=segment, domain=domain),
        prompts.get('Prompts', 'supplier_email_prompt').format(segment=segment, domain=domain),
        prompts.get('Prompts', 'internal_email_prompt').format(segment=segment, domain=domain)
    ]

    # Spinner for SMTP responses
    spinner = Halo(text='SMTP Contacting A.I service and generating responses (1/5)...', spinner='dots')
    spinner.start()
    try:
        smtp_raw_response = ai_service.query_responses(smtp_prompt, "smtp")
        smtp_cleaned_response = ai_service.cleanup_and_parse_json(smtp_raw_response)
        ai_service._store_responses(smtp_cleaned_response, "smtp")
        spinner.succeed('SMTP responses generated successfully.')
    except Exception as e:
        spinner.fail('Failed to generate SMTP responses.')

    # Spinner for POP3 responses
    spinner = Halo(text='POP3 Contacting A.I service and generating responses (2/5)...', spinner='dots')
    spinner.start()
    try:
        pop3_raw_response = ai_service.query_responses(pop3_prompt, "pop3")
        pop3_cleaned_response = ai_service.cleanup_and_parse_json(pop3_raw_response)
        ai_service._store_responses(pop3_cleaned_response, "pop3")
        spinner.succeed('POP3 responses generated successfully.')
    except Exception as e:
        spinner.fail('Failed to generate POP3 responses.')
        if debug_mode:
            logger.error(f"Error generating POP3 responses: {e}")

    # Spinner for sample emails
    total_emails = len(email_prompts)
    for i in range(total_emails):
        spinner = Halo(text=f'Contacting A.I service and generating sample email #{i+1} ({i+3}/5)...', spinner='dots')
        spinner.start()
        try:
            email_raw_response = ai_service.query_responses(email_prompts[i], f"email{i+1}")
            email_cleaned_response = ai_service.cleanup_and_parse_json(email_raw_response)
            ai_service.save_email_responses(email_cleaned_response, f"email{i+1}")
            spinner.succeed(f'Sample email #{i+1} generated successfully.')
        except Exception as e:
            spinner.fail(f'Failed to generate sample email #{i+1}.')
            if debug_mode:
                logger.error(f"Error generating sample email #{i+1}: {e}")

    # Update the config file with the technology, segment, domain, and anonymous access
    config.set('server', 'technology', technology)
    config.set('server', 'segment', segment)
    config.set('server', 'domain', domain)
    config.set('server', 'anonymous_access', str(anonymous_access))

    # Handle user credentials if anonymous access is not allowed
    if not anonymous_access:
        username = input("Enter username: ")
        password = input("Enter password: ")
        hashed_password = hash_password(password)
        config.set('server', 'username', username)
        config.set('server', 'password', hashed_password)
    else:
        if config.has_option('server', 'username'):
            config.remove_option('server', 'username')
        if config.has_option('server', 'password'):
            config.remove_option('server', 'password')

    # Save the updated configuration
    with open('etc/config.ini', 'w') as configfile:
        config.write(configfile)

    logger.info(f"Config file updated with anonymous_access: {anonymous_access}")

def main():
    """Main function to run the GenAIPot honeypot services."""
    ensure_files_directory()

    # Set up the database
    setup_database()

    Art = art.text2art("GenAIPot")
    print(Art)
    print("---------------------------------------")
    a = f"Version: {VERSION}"
    spinner = Halo(text=a, spinner='dots')    
    spinner.succeed()
    spinner = Halo(text="The first Generative A.I Honeypot", spinner='dots')
    spinner.stop_and_persist(symbol='🦄'.encode('utf-8'))

    if args.config or args.docker:
        run_config_wizard()
        return

    # Check for the presence of an OpenAI API key or 'no_ai' setting
    api_key = config.get('openai', 'api_key', fallback='')
    
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