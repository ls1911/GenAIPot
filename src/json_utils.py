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
This module provides utilities for handling JSON data, 
particularly for extracting and cleaning JSON from text.
"""

import json
import logging

logger = logging.getLogger(__name__)

def extract_and_clean_json(text):
    """
    Extract and clean JSON data from a given text.

    This function tries to find a JSON block within a text string, 
    extract it, and convert it to a Python dictionary.

    Args:
        text (str): The input text potentially containing JSON data.

    Returns:
        dict: The extracted JSON data as a dictionary.

    Raises:
        ValueError: If no JSON content is found or the extracted text is not valid JSON.
    """
    try:
        # Attempt to extract JSON block even if it's surrounded by additional text
        start = text.find('{')
        end = text.rfind('}') + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON content found")

        json_text = text[start:end]

        # Check if extracted text is valid JSON
        try:
            data = json.loads(json_text)
            return data
        except json.JSONDecodeError as e:
            logger.error("Error decoding JSON: %s", e)
            raise ValueError("Extracted text is not valid JSON") from e
    except Exception as e:
        logger.error("Error extracting JSON: %s", e)
        logger.debug("Raw text for cleanup: %s", text)
        raise ValueError("No JSON content found") from e

# Ensure to add a final newline at the end of the file
