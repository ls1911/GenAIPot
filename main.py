import logging
import argparse
import os
from twisted.internet import reactor
from smtp_protocol import SMTPFactory
#from genaipot.pop3.pop3_protocol import POP3Factory
from pop3.pop3_protocol import POP3Factory
from ai_services import AIService
import configparser
import datetime

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Read config file
config = configparser.ConfigParser()
config.read('config.ini')

def ensure_files_directory():
    if not os.path.exists('files'):
        os.makedirs('files')

def query_ai_service_for_responses(technology, segment, domain, anonymous_access):
    ai_service = AIService()

    # Query SMTP responses
    smtp_prompt = (
        f"Provide a detailed list of SMTP command responses for the {technology} "
        f"SMTP server in JSON format. The JSON should include common SMTP response codes "
        f"such as 220, 221, 250, 251, 354, 421, 450, 451, 452, 500, 501, 502, 503, 504, "
        f"550, 551, 552, 553, and 554, with appropriate messages."
    )
    smtp_raw_response = ai_service.query_responses(smtp_prompt, "smtp")
    smtp_cleaned_response = ai_service._extract_and_clean_json(smtp_raw_response)
    smtp_responses_path = ai_service._store_responses(smtp_cleaned_response, "smtp")

    # Query POP3 responses
    pop3_prompt = (
        f"Provide a detailed list of POP3 command responses for the {technology} "
        f"POP3 server in JSON format. The JSON should include common POP3 response codes "
        f"such as +OK, -ERR with appropriate messages."
    )
    pop3_raw_response = ai_service.query_responses(pop3_prompt, "pop3")
    pop3_cleaned_response = ai_service._extract_and_clean_json(pop3_raw_response)
    pop3_responses_path = ai_service._store_responses(pop3_cleaned_response, "pop3")

    # Query email examples
    email_prompts = [
    f"Generate an email for a client related to the segment: {segment}. The email should include a subject, body, and in the footer: "
    f"'Best Regards, [Realistic Full Name], [Job Position], {domain}'. Replace [Realistic Full Name] with a realistic full name, and [Job Position] with an appropriate job position.",
    
    f"Generate an email for a supplier related to the segment: {segment}. The email should include a subject, body, and in the footer: "
    f"'Best Regards, [Realistic Full Name], [Job Position], {domain}'. Replace [Realistic Full Name] with a realistic full name, and [Job Position] with an appropriate job position.",
    
    f"Generate an internal email related to the segment: {segment}. The email should include a subject, body, and in the footer: "
    f"'Best Regards, [Realistic Full Name], [Job Position], {domain}'. Replace [Realistic Full Name] with a realistic full name, and [Job Position] with an appropriate job position."
]
    
    for i, prompt in enumerate(email_prompts, 1):
        email_raw_response = ai_service.query_responses(prompt, f"email{i}")
        email_cleaned_response = ai_service.cleanup_and_parse_json(email_raw_response)
        ai_service.save_email_responses(email_cleaned_response, f"email{i}")

    ai_service.update_config_technology(technology)
    ai_service.update_config_segment(segment)
    ai_service.update_config_domain(domain)
    ai_service.update_config_anonymous_access(anonymous_access)

def main():
    ensure_files_directory()

    parser = argparse.ArgumentParser(description="GenAIPot Honeypot Configuration")
    parser.add_argument("--config", action="store_true", help="Configure the honeypot with AI-generated responses")
    parser.add_argument("--smtp", action="store_true", help="Start the SMTP honeypot service")
    parser.add_argument("--pop3", action="store_true", help="Start the POP3 honeypot service")
    parser.add_argument("--all", action="store_true", help="Start both SMTP and POP3 honeypot services")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

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
            logger.info(f"Starting GenAIPot Version 0.3.1")
            if args.debug:
                start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Start Time: {start_time}")
                logger.info(f"IP: {config.get('server', 'ip', fallback='localhost')}")
                logger.info(f"Listening Ports: 25")
                logger.info(f"SQLite Logging Enabled: {config.getboolean('logging', 'sqlite', fallback=True)}")
                logger.info(f"Server Technology: {config.get('server', 'technology', fallback='generic')}")
                logger.info(f"Domain Name: {config.get('server', 'domain', fallback='localhost')}")

            smtp_factory = SMTPFactory()
            reactor.listenTCP(25, smtp_factory)
            logger.info("SMTP honeypot started on port 25")
        except Exception as e:
            logger.error(f"Failed to start SMTP honeypot: {e}")

    if args.pop3 or args.all:
        try:
            logger.info(f"Starting GenAIPot Version 0.3.1")
            if args.debug:
                start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Start Time: {start_time}")
                logger.info(f"IP: {config.get('server', 'ip', fallback='localhost')}")
                logger.info(f"Listening Ports: 110")
                logger.info(f"SQLite Logging Enabled: {config.getboolean('logging', 'sqlite', fallback=True)}")
                logger.info(f"Server Technology: {config.get('server', 'technology', fallback='generic')}")
                logger.info(f"Domain Name: {config.get('server', 'domain', fallback='localhost')}")

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