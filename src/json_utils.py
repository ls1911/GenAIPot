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

import json
import logging

logger = logging.getLogger(__name__)

def extract_and_clean_json(text):
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
            logger.error(f"Error decoding JSON: {e}")
            raise ValueError("Extracted text is not valid JSON")
    except Exception as e:
        logger.error(f"Error extracting JSON: {e}")
        logger.debug(f"Raw text for cleanup: {text}")
        raise ValueError("No JSON content found")