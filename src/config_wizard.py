import os
import shutil
from halo import Halo
import configparser
from ai_services import validate_openai_key, validate_azure_key, query_ai_service_for_responses, AIService

def run_config_wizard(args, config, config_file_path):
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
    provider_choice = input("Choose the AI provider to use:\n"
                            "1. OpenAI (Working)\n"
                            "2. Azure OpenAI (Work In Progress)\n"
                            "3. Google Vertex AI (Work In Progress)\n"
                            "4. Offline (Use pre-existing templates)\n"
                            "Enter the number of your choice: ")

    ai_service = None  # Initialize the ai_service variable
    
    if provider_choice == '1':
        provider = 'openai'
        openai_key = input("Enter your OpenAI API key: ")

        # Validate the OpenAI key before proceeding        
        with Halo(text="Validating OpenAI API key...", spinner='dots') as spinner:
            if not validate_openai_key(openai_key):
                spinner.fail("Invalid API key.")
                exit(1)
            else:
                spinner.succeed("API key is valid.")

        if not config.has_section('openai'):
            config.add_section('openai')
        config.set('openai', 'api_key', openai_key)

        # Initialize AIService for querying later (generic service class)
        ai_service = AIService(api_key=openai_key, debug_mode=args.debug)  # Removed 'provider'

    elif provider_choice == '2':
        provider = 'azure'
        azure_key = input("Enter your Azure OpenAI API key: ")
        azure_endpoint = input("Enter your Azure OpenAI endpoint: ")
        azure_location = input("Enter your Azure OpenAI location/region: ")

        # Validate the Azure API key and endpoint before proceeding
        with Halo(text="Validating Azure OpenAI API key and endpoint...", spinner='dots') as spinner:
            if not validate_azure_key(azure_key, azure_endpoint, azure_location):
                spinner.fail("Invalid API key or endpoint.")
                exit(1)
            else:
                spinner.succeed("API key and endpoint are valid.")

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

        # Exit with a message for unsupported integration
        exit('Oh no!\nSnap!\nGoogle is charging us to develop integration with them!\nOther provider is recommended.\nIf you don’t have other provider access, try the offline mode!\nXOXO :-*')

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
    technology_choice = input("Choose the server technology to emulate:\n"
                              "a. sendmail\n"
                              "b. exchange\n"
                              "c. qmail\n"
                              "d. postfix\n"
                              "e. zimbra\n"
                              "f. other\n"
                              "Enter the letter of your choice: ")
    technology = {
        'a': 'sendmail',
        'b': 'exchange',
        'c': 'qmail',
        'd': 'postfix',
        'e': 'zimbra',
        'f': 'other'
    }.get(technology_choice.lower(), 'generic')  # Default to 'generic' if invalid input
    
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

    # Query the AI service for responses if not in offline mode
    if provider != 'offline' and ai_service:
        query_ai_service_for_responses(technology, segment, domain, anonymous_access, args.debug, ai_service)