import logging
import argparse
import os
import configparser
import datetime
from twisted.internet import reactor
from smtp_protocol import SMTPFactory
from pop3.pop3_protocol import POP3Factory
from ai_services import AIService
from auth import check_credentials, hash_password

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read config file
config = configparser.ConfigParser()
config.read('config.ini')
prompts = configparser.ConfigParser()
prompts.read('prompts.ini')

VERSION = "0.3.2"

def ensure_files_directory():
    """Ensure the existence of the 'files' directory."""
    if not os.path.exists('files'):
        os.makedirs('files')

def query_ai_service_for_responses(technology, segment, domain, anonymous_access):
    """
    Query the AI service for SMTP and POP3 responses and sample emails.

    Args:
        technology (str): The technology used (e.g., sendmail, exchange).
        segment (str): The segment of the industry or application.
        domain (str): The domain name for the service.
        anonymous_access (bool): Whether anonymous access is allowed.
    """
    ai_service = AIService(debug_mode=args.debug)

    # Load prompts from prompts.ini
    smtp_prompt = prompts.get('Prompts', 'smtp_prompt').format(technology=technology)
    pop3_prompt = prompts.get('Prompts', 'pop3_prompt').format(technology=technology)
    email_prompts = [
        prompts.get('Prompts', 'client_email_prompt').format(segment=segment, domain=domain),
        prompts.get('Prompts', 'supplier_email_prompt').format(segment=segment, domain=domain),
        prompts.get('Prompts', 'internal_email_prompt').format(segment=segment, domain=domain)
    ]

    # Query SMTP responses
    logger.info("Generating service responses for SMTP...")
    smtp_raw_response = ai_service.query_responses(smtp_prompt, "smtp")
    smtp_cleaned_response = ai_service.cleanup_and_parse_json(smtp_raw_response)
    ai_service._store_responses(smtp_cleaned_response, "smtp")

    # Query POP3 responses
    logger.info("Generating service responses for POP3...")
    pop3_raw_response = ai_service.query_responses(pop3_prompt, "pop3")
    pop3_cleaned_response = ai_service.cleanup_and_parse_json(pop3_raw_response)
    ai_service._store_responses(pop3_cleaned_response, "pop3")

    # Query email examples
    logger.info("Generating sample emails...")
    for i, prompt in enumerate(email_prompts, 1):
        email_raw_response = ai_service.query_responses(prompt, f"email{i}")
        email_cleaned_response = ai_service.cleanup_and_parse_json(email_raw_response)
        ai_service.save_email_responses(email_cleaned_response, f"email{i}")

    # Update the config file with the technology, segment, domain, and anonymous access
    ai_service.update_config_technology(technology)
    ai_service.update_config_segment(segment)
    ai_service.update_config_domain(domain)
    ai_service.update_config_anonymous_access(anonymous_access)

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
    config.set('server', 'anonymous_access', str(anonymous_access))
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

    logger.info(f"Config file updated with anonymous_access: {anonymous_access}")

def main():
    """Main function to run the GenAIPot honeypot services."""
    ensure_files_directory()

    parser = argparse.ArgumentParser(description="GenAIPot Honeypot Configuration")
    parser.add_argument("--config", action="store_true", help="Configure the honeypot with AI-generated responses")
    parser.add_argument("--smtp", action="store_true", help="Start the SMTP honeypot service")
    parser.add_argument("--pop3", action="store_true", help="Start the POP3 honeypot service")
    parser.add_argument("--all", action="store_true", help="Start both SMTP and POP3 honeypot services")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode is enabled.")
    else:
        logging.basicConfig(level=logging.INFO)

    if args.config:
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
        
        segment = input("Enter the segment: ")
        domain = input("Enter the domain name: ")
        anonymous_access = input("Allow anonymous access? (y/n): ").lower() == 'y'
        query_ai_service_for_responses(technology, segment, domain, anonymous_access)
        return

    if args.smtp or args.all:
        try:
            logger.info(f"Starting GenAIPot Version {VERSION}")
            if args.debug:
                start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Start Time: {start_time}")
                logger.info(f"IP: {config.get('server', 'ip', fallback='localhost')}")
                logger.info(f"Listening Ports: 25")
                logger.info(f"SQLite Logging Enabled: {config.getboolean('logging', 'sqlite', fallback=True)}")
                logger.info(f"Server Technology: {config.get('server', 'technology', fallback='generic')}")
                logger.info(f"Domain Name: {config.get('server', 'domain', fallback='localhost')}")
                logging.getLogger('urllib3').setLevel(logging.DEBUG)

            smtp_factory = SMTPFactory()
            reactor.listenTCP(25, smtp_factory)
            logger.info("SMTP honeypot started on port 25")
        except Exception as e:
            logger.error(f"Failed to start SMTP honeypot: {e}")

    if args.pop3 or args.all:
        try:
            logger.info(f"Starting GenAIPot Version {VERSION}")
            if args.debug:
                start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Start Time: {start_time}")
                logger.info(f"IP: {config.get('server', 'ip', fallback='localhost')}")
                logger.info(f"Listening Ports: 110")
                logger.info(f"SQLite Logging Enabled: {config.getboolean('logging', 'sqlite', fallback=True)}")
                logger.info(f"Server Technology: {config.get('server', 'technology', fallback='generic')}")
                logger.info(f"Domain Name: {config.get('server', 'domain', fallback='localhost')}")
                logging.getLogger('urllib3').setLevel(logging.DEBUG)

            pop3_factory = POP3Factory()
            reactor.listenTCP(110, pop3_factory)
            logger.info("POP3 honeypot started on port 110")
        except Exception as e:
            logger.error(f"Failed to start POP3 honeypot: {e}")

    if args.smtp or args.pop3 or args.all:
        logger.info("Reactor is running...")
        reactor.run()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()