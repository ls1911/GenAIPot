import logging

def save_raw_response(response_text, response_type):
    """
    Save the raw response text to a file.
    
    Args:
        response_text (str): The response text from the AI service.
        response_type (str): The type of response (e.g., "email").
    """
    filename = f'files/{response_type}_raw_response.txt'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(response_text)
    logging.debug(f"Raw response saved in {filename}")