import hashlib
import logging
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

logger = logging.getLogger(__name__)

def hash_password(password):
    """
    Hash the provided password using a secure hashing algorithm.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(username, password):
    """
    Check if the provided credentials match the stored credentials.
    """
    stored_username = config.get('server', 'username')
    stored_password = config.get('server', 'password')  # This is the hashed password

    # Hash the provided password to compare with stored hash
    hashed_password = hash_password(password)
    
    if config.getboolean('server', 'debug', fallback=False):
        logger.debug(f"Checking credentials for user: {username}")
        logger.debug(f"Provided password (hashed): {hashed_password}")
        logger.debug(f"Stored username: {stored_username}")
        logger.debug(f"Stored password (hashed): {stored_password}")

    if username == stored_username and hashed_password == stored_password:
        return True
    else:
        return False