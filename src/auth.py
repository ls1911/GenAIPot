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