from protocol import PROTOCOL_VERSION


SUPPORTED_COMMANDS = {
    "HELLO",
    "LIST",
    "CHECKOUT",
    "RETURN",
    "MY_ITEMS",
    "QUIT"
}


def validate_request(message):
    if not isinstance(message, dict):
        return False, "INVALID_MESSAGE", "Request must be a JSON object."

    if "version" not in message:
        return False, "MISSING_FIELD", "version is required."

    if message["version"] != PROTOCOL_VERSION:
        return False, "UNSUPPORTED_VERSION", "Unsupported protocol version."

    if "type" not in message:
        return False, "MISSING_FIELD", "type is required."

    if message["type"] != "request":
        return False, "INVALID_FIELD", "type must be 'request'."

    if "request_id" not in message:
        return False, "MISSING_FIELD", "request_id is required."

    request_id = message["request_id"]

    if (
        not isinstance(request_id, str)
        or not request_id.strip()
        or len(request_id) > 32
    ):
        return (
            False,
            "INVALID_FIELD",
            "request_id must be a non-empty string of at most 32 characters."
        )

    if "command" not in message:
        return False, "MISSING_FIELD", "command is required."

    command = message["command"]

    if not isinstance(command, str):
        return False, "INVALID_FIELD", "command must be a string."

    if command not in SUPPORTED_COMMANDS:
        return False, "UNKNOWN_COMMAND", f"Unsupported command: {command}"

    if "data" not in message:
        return False, "MISSING_FIELD", "data is required."

    if not isinstance(message["data"], dict):
        return False, "INVALID_FIELD", "data must be a JSON object."

    return validate_command_data(command, message["data"])


def validate_command_data(command, data):
    if command == "HELLO":
        if "username" not in data:
            return False, "MISSING_FIELD", "username is required."

        username = data["username"]

        if not isinstance(username, str) or not username.strip():
            return False, "INVALID_FIELD", "username must be a non-empty string."

        if len(username) > 50:
            return False, "INVALID_FIELD", "username must be 50 characters or fewer."

    elif command in {"CHECKOUT", "RETURN"}:
        if "equipment_id" not in data:
            return False, "MISSING_FIELD", "equipment_id is required."

        equipment_id = data["equipment_id"]

        if isinstance(equipment_id, bool) or not isinstance(equipment_id, int):
            return False, "INVALID_FIELD", "equipment_id must be an integer."

        if equipment_id <= 0:
            return False, "INVALID_FIELD", "equipment_id must be greater than zero."

    return True, None, None
