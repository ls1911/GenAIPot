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

import os
import shutil
from halo import Halo
import configparser
from ai_services import validate_openai_key, validate_azure_key, query_ai_service_for_responses, AIService
import getpass
import logging

def ensure_files_directory():
    """Ensure the existence of the 'files' directory."""
    if not os.path.exists('files'):
        os.makedirs('files')

def run_config_wizard(args, config, config_file_path):
    """Runs the configuration wizard to set up the honeypot."""
    ensure_files_directory()
    
    if args.docker:
        print("Using Docker mode. Copying default configuration files without prompting.")
        config_src = os.path.join('var/no_ai', 'config.ini')
        config_dst = os.path.join('etc', 'config.ini')
        if os.path.exists(config_src):
            shutil.copyfile(config_src, config_dst)
            print("Default configuration has been applied for Docker.")
        else:
            print(f"Config file not found at {config_src}")
        return

    # Check if config.ini or files/ directory already exist
    config_exists = os.path.exists(config_file_path)
    files_exist = os.path.exists('files') and os.listdir('files')

    if config_exists or files_exist:
        overwrite = input("Configuration files already exist. Do you want to overwrite them? (y/n): ").lower()
        if overwrite != 'y':
            print("Exiting without changes.")
            return
        
        # If user wants to overwrite, delete old files
        if config_exists:
            os.remove(config_file_path)
            print("Old configuration file deleted.")
        if files_exist:
            shutil.rmtree('files')
            print("Old AI-generated files deleted.")

    # Ask the user to select the AI provider
    valid_providers = {'1', '2', '3', '4'}
    provider_choice = ''
    while provider_choice not in valid_providers:
        provider_choice = input("Choose the AI provider to use:\n"
                                "1. OpenAI (Working)\n"
                                "2. Azure OpenAI (Work In Progress)\n"
                                "3. Google Vertex AI (Work In Progress)\n"
                                "4. Offline (Use pre-existing templates)\n"
                                "Enter the number of your choice: ")
        if provider_choice not in valid_providers:
            print("Invalid choice. Please enter a number between 1 and 4.")

    ai_service = None  # Initialize the ai_service variable
    
    if provider_choice == '1':
        provider = 'openai'
        while True:
            openai_key = getpass.getpass("Enter your OpenAI API key: ")  # Use getpass to hide the API key
            # Validate the OpenAI key before proceeding        
            with Halo(text="Validating OpenAI API key...", spinner='dots') as spinner:
                if not validate_openai_key(openai_key):
                    spinner.fail("Invalid or empty API key.")
                    retry = input("API key validation failed. Do you want to re-enter the API key? (y/n): ").lower()
                    if retry != 'y':
                        print("Exiting configuration wizard.")
                        return
                else:
                    spinner.succeed("API key is valid.")
                    break

        if not config.has_section('openai'):
            config.add_section('openai')
        config.set('openai', 'api_key', openai_key)

        # Initialize AIService for querying later (generic service class)
        ai_service = AIService(api_key=openai_key, debug_mode=args.debug)

    elif provider_choice == '2':
        provider = 'azure'
        while True:
            azure_key = input("Enter your Azure OpenAI API key: ")
            azure_endpoint = input("Enter your Azure OpenAI endpoint: ")
            azure_location = input("Enter your Azure OpenAI location/region: ")

            # Validate the Azure API key and endpoint before proceeding
            with Halo(text="Validating Azure OpenAI API key and endpoint...", spinner='dots') as spinner:
                if not validate_azure_key(azure_key, azure_endpoint, azure_location):
                    spinner.fail("Invalid API key or endpoint.")
                    retry = input("API key validation failed. Do you want to re-enter the details? (y/n): ").lower()
                    if retry != 'y':
                        print("Exiting configuration wizard.")
                        return
                else:
                    spinner.succeed("API key and endpoint are valid.")
                    break

        # Store configuration in the config file
        if not config.has_section('azure'):
            config.add_section('azure')
        config.set('azure', 'api_key', azure_key)
        config.set('azure', 'endpoint', azure_endpoint)
        config.set('azure', 'location', azure_location)

        # Initialize AIService for querying later
        ai_service = AIService(api_key=azure_key, azure_endpoint=azure_endpoint, azure_location=azure_location, debug_mode=args.debug)

    elif provider_choice == '3':
        provider = 'gcp'
        print('Oh no!\nSnap!\nGoogle is charging us to develop integration with them!\nOther provider is recommended.\nIf you don’t have other provider access, try the offline mode!\nXOXO :-*')
        exit(1)

    elif provider_choice == '4':
        provider = 'offline'
        print("Using offline mode with pre-existing configuration.")
        
        # Paths for the source and destination directories
        config_src = os.path.join('var/no_ai', 'config.ini')
        config_dst = os.path.join('etc', 'config.ini')
        files_src = os.path.join('var/no_ai/')
        files_dst = 'files/'

        # Copy config.ini to etc/
        if os.path.exists(config_src):
            shutil.copyfile(config_src, config_dst)
            print(f"Copied config.ini to {config_dst}.")
        else:
            print(f"Config file not found at {config_src}. Exiting.")
            exit(1)

        # Ensure the destination 'files/' directory exists
        if not os.path.exists(files_dst):
            os.makedirs(files_dst)

        # List of files to copy
        files_to_copy = [
            'email1_raw_response.txt',
            'email2_raw_response.txt',
            'email3_raw_response.txt',
            'pop3_raw_response.txt',
            'pop3_responses.json',
            'smtp_raw_response.txt',
            'smtp_responses.json'
        ]

        # Copy the necessary files to the files/ directory
        for file_name in files_to_copy:
            src_file = os.path.join(files_src, file_name)
            dst_file = os.path.join(files_dst, file_name)
            if os.path.exists(src_file):
                shutil.copyfile(src_file, dst_file)
                print(f"Copied {file_name} to {dst_file}.")
            else:
                print(f"File {file_name} not found in {files_src}. Skipping.")
        
        print("Offline configuration and files copied successfully.")
        exit()

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
    valid_technologies = {'a', 'b', 'c', 'd', 'e', 'f'}
    technology_choice = ''
    while technology_choice.lower() not in valid_technologies:
        technology_choice = input("Choose the server technology to emulate:\n"
                                  "a. sendmail\n"
                                  "b. exchange\n"
                                  "c. qmail\n"
                                  "d. postfix\n"
                                  "e. zimbra\n"
                                  "f. other\n"
                                  "Enter the letter of your choice: ")
        if technology_choice.lower() not in valid_technologies:
            print("Invalid choice. Please enter a letter between 'a' and 'f'.")

    technology = {
        'a': 'sendmail',
        'b': 'exchange',
        'c': 'qmail',
        'd': 'postfix',
        'e': 'zimbra',
        'f': 'other'
    }[technology_choice.lower()]

    segment = input("Enter the segment (industry description): ")
    domain = input("Enter the domain name (fictional company): ")

    anonymous_access_input = ''
    while anonymous_access_input.lower() not in {'y', 'n'}:
        anonymous_access_input = input("Allow anonymous access? (y/n): ").lower()
        if anonymous_access_input.lower() not in {'y', 'n'}:
            print("Invalid choice. Please enter 'y' or 'n'.")
    anonymous_access = anonymous_access_input == 'y'

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
            return

    # Query the AI service for responses if not in offline mode
    if provider != 'offline' and ai_service:
        try:
            query_ai_service_for_responses(technology, segment, domain, anonymous_access, args.debug, ai_service)
        except Exception as e:
            print(f"An error occurred while generating AI responses: {e}")
            if args.debug:
                logging.exception("Error during AI response generation")
            retry = input("Do you want to retry generating AI responses? (y/n): ").lower()
            if retry == 'y':
                query_ai_service_for_responses(technology, segment, domain, anonymous_access, args.debug, ai_service)
            else:
                print("Skipping AI response generation.")