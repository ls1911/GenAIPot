import logging
from twisted.protocols.basic import LineReceiver
from twisted.internet import protocol
from pop3.pop3_utils import generate_email_headers
from database import log_interaction
import configparser
import os
from auth import check_credentials

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini')
domain_name = config.get('server', 'domain', fallback='localhost')
technology = config.get('server', 'technology', fallback='generic')

class POP3Protocol(LineReceiver):
    def __init__(self, debug=False):
        self.ip = None
        self.responses = self.load_responses()
        self.state = 'AUTHORIZATION'
        self.user = None
        self.passwd = None
        self.emails = self.load_raw_emails()
        self.deleted_emails = set()
        self.debug = debug
        logging.basicConfig(level=logging.DEBUG)

        if self.debug:
            
            logger.debug(f"POP3Protocol initialized with {len(self.emails)} emails loaded.")

    def connectionMade(self):
        self.ip = self.transport.getPeer().host
        banner = self.responses.get("+OK", f"+OK {domain_name} {technology} POP3 server ready")
        logger.info(f"Connection from {self.ip}")
        self.sendLine(banner.encode('utf-8'))
        log_interaction(self.ip, 'WELCOME', banner)

    def lineReceived(self, line):
        try:
            command = line.decode('utf-8').strip().upper()
            logger.info(f"Received command: {command}")
            if command == 'QUIT':
                response = "+OK Goodbye"
                self.sendLine(response.encode('utf-8'))
                self.transport.loseConnection()
                return
            
            if self.state == 'TRANSACTION':
                response = self.handle_pop3_command(command)
            elif self.state == 'AUTHORIZATION':
                response = self.handle_authorization(command)
            else:
                response = "-ERR Command not allowed in this state"
            if response:
                self.sendLine(response.encode('utf-8'))
                log_interaction(self.ip, command, response)
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error: {e}")
            self.sendLine(b"-ERR Command unrecognized")

    def load_responses(self):
        try:
            with open(f'files/{technology}_pop3_raw_response.txt', 'r') as f:
                raw_responses = f.read()
                logger.info(f"Loaded responses from files/{technology}_pop3_raw_response.txt")
                return self.format_responses(raw_responses)
        except FileNotFoundError:
            logger.warning(f"Response file files/{technology}_pop3_raw_response.txt not found. Using default responses.")
            return self.default_pop3_responses()
        except Exception as e:
            logger.error(f"Error loading responses: {e}")
            return self.default_pop3_responses()

    def format_responses(self, raw_responses):
        response_dict = {}
        lines = raw_responses.splitlines()
        for line in lines:
            if line.startswith('+OK') or line.startswith('-ERR'):
                key = line.split(' ', 1)[0]
                response_dict[key] = line
        return response_dict

    def default_pop3_responses(self):
        return {
            "+OK": f"+OK {domain_name} {technology} POP3 server ready",
            "-ERR": "-ERR Default error response"
        }

    def load_raw_emails(self):
        emails = {}
        for i in range(1, 4):
            filename = f'files/email{i}_raw_response.txt'
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    emails[i] = f.read()
                    logger.info(f"Loaded email content from {filename}")
            else:
                logger.warning(f"Email file {filename} not found.")
        return emails

    def handle_pop3_command(self, command):
        if command == 'STAT':
            num_messages = len(self.emails) - len(self.deleted_emails)
            total_size = sum(len(email) for i, email in self.emails.items() if i not in self.deleted_emails)
            return f"+OK {num_messages} {total_size}"
        elif command == 'LIST':
            response = "+OK maildrop follows\n"
            for i, email in self.emails.items():
                if i not in self.deleted_emails:
                    response += f"{i} {len(email)}\n"
            response += "."
            return response
        elif command.startswith('RETR'):
            try:
                msg_num = int(command.split()[1])
                if msg_num in self.emails and msg_num not in self.deleted_emails:
                    email_body = self.emails[msg_num]
                    headers = generate_email_headers(email_body)
                    email_content = headers + "\n" + email_body
                    return f"+OK {len(email_content)} octets\n{email_content}"
                else:
                    return "-ERR no such message"
            except (IndexError, ValueError):
                return "-ERR syntax: RETR <msg>"
        elif command.startswith('DELE'):
            try:
                msg_num = int(command.split()[1])
                if msg_num in self.emails:
                    self.deleted_emails.add(msg_num)
                    return f"+OK message {msg_num} deleted"
                else:
                    return "-ERR no such message"
            except (IndexError, ValueError):
                return "-ERR syntax: DELE <msg>"
        elif command == 'QUIT':
            response = self.responses.get("QUIT", "+OK Goodbye")
            self.sendLine(response.encode('utf-8'))
            self.transport.loseConnection()
            return None
        else:
            return "-ERR Unrecognized command"

    def handle_authorization(self, command):
        command = command.upper()
        if command.startswith('USER'):
            self.user = command.split(' ')[1].lower() if len(command.split(' ')) > 1 else None
            
            if self.user:
                logger.debug(f"USER command received. Entered user: {self.user}")
                if config.get('server', 'anonymous_access', fallback='True') == 'False':
                    stored_username = config.get('server', 'username', fallback=None)
                    
                    logger.debug(f"Stored username: {stored_username}")
                    if stored_username and stored_username == self.user:
                        return "+OK User accepted"
                    else:
                        return "-ERR Invalid username"
                return "+OK User accepted"
            else:
                return "-ERR Missing username"

        elif command.startswith('PASS'):
            self.passwd = command.split(' ')[1].lower() if len(command.split(' ')) > 1 else None
            if self.passwd:
                stored_password = config.get('server', 'password', fallback=None)
                logger.debug(f"Entered password: {self.passwd}")
                logger.debug(f"Stored password (hashed): {stored_password}")
                if config.get('server', 'anonymous_access', fallback='True') == 'True':
                    logger.debug("Anonymous access enabled; skipping password check.")
                    self.state = 'TRANSACTION'
                    return "+OK Password accepted"
                elif stored_password and check_credentials(self.user, self.passwd):
                    logger.debug("PASS command received. Password verified. Moving to TRANSACTION state.")
                    self.state = 'TRANSACTION'
                    return "+OK Password accepted"
                else:
                    logger.debug("PASS command received. Password incorrect.")
                    self.user = None
                    self.passwd = None
                    return "-ERR Invalid username or password"
            else:
                return "-ERR Missing password"

        else:
            return "-ERR Unrecognized command"

class POP3Factory(protocol.Factory):
    def __init__(self, debug=False):
        self.debug = debug

    def buildProtocol(self, addr):
        print("Building POP3 protocol with debug =", self.debug)
        if self.debug:
            logging.basicConfig(level=logging.DEBUG)
        return POP3Protocol(debug=self.debug)