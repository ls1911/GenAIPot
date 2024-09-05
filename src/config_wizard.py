import os
import shutil
from halo import Halo
import configparser
from ai_services import validate_openai_key
from ai_services import query_ai_service_for_responses

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
                            "1. OpenAI\n"
                            "2. Azure OpenAI\n"
                            "3. Google Vertex AI\n"
                            "4. Offline (use pre-existing templates)\n"
                            "Enter the number of your choice: ")

    if provider_choice == '1':
        provider = 'openai'
        openai_key = input("Enter your OpenAI API key: ")

        # Validate the OpenAI key before proceeding
        with Halo(text="Validating OpenAI API key...", spinner='dots') as spinner:
            if not validate_openai_key(openai_key, ai_service):
                spinner.fail("Invalid OpenAI API key. Exiting.")
                return
            spinner.succeed("API key is valid.")
        
        if not config.has_section('openai'):
            config.add_section('openai')
        config.set('openai', 'api_key', openai_key)

    elif provider_choice == '2':
        provider = 'azure'
        azure_key = input("Enter your Azure OpenAI API key: ")
        azure_endpoint = input("Enter your Azure OpenAI endpoint: ")

        # Assuming we also want to validate the Azure OpenAI key (validation logic should be added)
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

    if provider != 'offline':
        query_ai_service_for_responses(technology, segment, domain, anonymous_access, ai_service)