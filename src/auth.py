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

"""
This module provides authentication utilities for GenAIPot, 
including password hashing and credential checking.
"""

import hashlib
import logging
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

logger = logging.getLogger(__name__)

def hash_password(password):
    """
    Hash the provided password using SHA-256.

    Args:
        password (str): The password to hash.

    Returns:
        str: The hashed password.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(username, password):
    """
    Check if the provided credentials match the stored credentials.

    Args:
        username (str): The username to check.
        password (str): The password to check.

    Returns:
        bool: True if the credentials match, False otherwise.
    """
    stored_username = config.get('server', 'username')
    stored_password = config.get('server', 'password')  # This is the hashed password

    # Hash the provided password to compare with stored hash
    hashed_password = hash_password(password)

    if config.getboolean('server', 'debug', fallback=False):
        logger.debug("Checking credentials for user: %s", username)
        logger.debug("Provided password (hashed): %s", hashed_password)
        logger.debug("Stored username: %s", stored_username)
        logger.debug("Stored password (hashed): %s", stored_password)

    return username == stored_username and hashed_password == stored_password

# Ensure to add a final newline at the end of the file
