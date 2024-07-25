import logging
from pop3.pop3_utils import format_responses, log_interaction

logger = logging.getLogger(__name__)

def handle_authorization(protocol, command):
    """
    Handle the authorization phase of the POP3 protocol.

    This function processes USER and PASS commands to authenticate the user.
    If the user is authenticated, the state transitions to TRANSACTION.

    Args:
        protocol: The current protocol instance.
        command (str): The command issued by the client.

    Returns:
        str: A response string indicating the result of the command.
    """
    command_upper = command.upper()
    if command_upper.startswith("USER"):
        protocol.user = command.split(" ", 1)[1] if len(command.split(" ", 1)) > 1 else None
        if protocol.user:
            logger.debug(f"USER command received. User set to: {protocol.user}")
            return "+OK User accepted"
        return "-ERR Missing username"
    elif command_upper.startswith("PASS"):
        protocol.passwd = command.split(" ", 1)[1] if len(command.split(" ", 1)) > 1 else None
        if protocol.passwd:
            protocol.state = 'TRANSACTION'
            logger.debug(f"PASS command received. Password set. Moving to TRANSACTION state.")
            return "+OK Password accepted"
        return "-ERR Missing password"
    return "-ERR Please authenticate first"

def handle_transaction(protocol, command):
    """
    Handle the transaction phase of the POP3 protocol.

    This function processes various commands such as STAT, LIST, RETR, DELE, and QUIT,
    which operate on the emails available in the session.

    Args:
        protocol: The current protocol instance.
        command (str): The command issued by the client.

    Returns:
        str: A response string indicating the result of the command.
    """
    command_upper = command.upper()
    if command_upper.startswith("STAT"):
        return _handle_stat(protocol)
    elif command_upper.startswith("LIST"):
        return _handle_list(protocol)
    elif command_upper.startswith("RETR"):
        return _handle_retr(protocol, command)
    elif command_upper.startswith("DELE"):
        return _handle_dele(protocol, command)
    elif command_upper.startswith("QUIT"):
        return _handle_quit(protocol, command)
    return "-ERR Command unrecognized"

def _handle_stat(protocol):
    """
    Handle the STAT command which provides statistics about the mailbox.

    Args:
        protocol: The current protocol instance.

    Returns:
        str: A response string with the number of messages and the total size.
    """
    total_emails = len([e for i, e in enumerate(protocol.emails) if i not in protocol.deleted_emails])
    total_size = sum(email['size'] for i, email in enumerate(protocol.emails) if i not in protocol.deleted_emails)
    logger.debug(f"STAT command: {total_emails} messages, {total_size} total size.")
    return f"+OK {total_emails} {total_size}"

def _handle_list(protocol):
    """
    Handle the LIST command which lists the messages available in the mailbox.

    Args:
        protocol: The current protocol instance.

    Returns:
        str: A response string with the list of messages and their sizes.
    """
    valid_emails = [(i, email) for i, email in enumerate(protocol.emails) if i not in protocol.deleted_emails]
    if not valid_emails:
        return "+OK 0 messages"
    response = f"+OK {len(valid_emails)} messages"
    for i, (index, email) in enumerate(valid_emails, start=1):
        size = email['size']
        response += f"\n{i} {size}"
    logger.debug(f"LIST command response: {response}")
    return response

def _handle_retr(protocol, command):
    """
    Handle the RETR command which retrieves the full content of a specified message.

    Args:
        protocol: The current protocol instance.
        command (str): The RETR command with the message number.

    Returns:
        str: A response string with the full content of the message, or an error message if the message number is invalid.
    """
    try:
        msg_number = int(command.split(" ")[1])
        valid_emails = [(i, email) for i, email in enumerate(protocol.emails) if i not in protocol.deleted_emails]
        if 1 <= msg_number <= len(valid_emails):
            _, email = valid_emails[msg_number - 1]
            return f"+OK {email['size']} octets\n{email['content']}"
        return "-ERR Message number out of range"
    except (IndexError, ValueError):
        return "-ERR Syntax error in parameters or arguments"

def _handle_dele(protocol, command):
    """
    Handle the DELE command which marks a specified message for deletion.

    Args:
        protocol: The current protocol instance.
        command (str): The DELE command with the message number.

    Returns:
        str: A response string indicating whether the message was successfully marked for deletion or an error occurred.
    """
    try:
        msg_number = int(command.split(" ")[1]) - 1
        if 0 <= msg_number < len(protocol.emails) and msg_number not in protocol.deleted_emails:
            protocol.deleted_emails.add(msg_number)
            logger.debug(f"DELE command: Marked message {msg_number + 1} for deletion.")
            return "+OK Message marked for deletion"
        return "-ERR No such message"
    except (IndexError, ValueError):
        return "-ERR Syntax error in parameters or arguments"

def _handle_quit(protocol, command):
    """
    Handle the QUIT command which ends the session and closes the connection.

    Args:
        protocol: The current protocol instance.
        command (str): The QUIT command.

    Returns:
        str: A response string indicating the session has ended and the connection is being closed.
    """
    response = "+OK POP3 server signing off"
    log_interaction(protocol.ip, command, response)
    protocol.transport.loseConnection()
    logger.debug("QUIT command received. Connection closing.")
    return response