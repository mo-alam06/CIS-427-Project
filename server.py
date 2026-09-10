import logging
import socket
import sys

from equipment import EquipmentManager
from protocol import PROTOCOL_VERSION, encode_message, extract_frames, decode_frame
from validation import validate_request


logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    encoding="utf-8"
)

logger = logging.getLogger("CampusGearServer")


def success_response(request_id, data=None):
    return {
        "version": PROTOCOL_VERSION,
        "type": "response",
        "request_id": request_id,
        "ok": True,
        "data": data or {}
    }


def error_response(request_id, code, message):
    return {
        "version": PROTOCOL_VERSION,
        "type": "response",
        "request_id": request_id,
        "ok": False,
        "error": {
            "code": code,
            "message": message
        }
    }


def send_response(client_socket, response):
    client_socket.sendall(encode_message(response))


def protocol_error_message(error_code):
    messages = {
        "MALFORMED_JSON": "The request contains malformed JSON.",
        "EMPTY_MESSAGE": "The request message is empty.",
        "MESSAGE_TOO_LARGE": "The request exceeds the maximum message size.",
        "INVALID_MESSAGE": "The request is not a valid protocol message."
    }
    return messages.get(error_code, "Invalid protocol message.")


def handle_client(client_socket, client_address, equipment_manager):
    buffer = b""
    session_active = True
    session_username = None
    client_id = f"{client_address[0]}:{client_address[1]}"

    logger.info("Client connected from %s", client_id)
    print(f"Client connected from {client_id}")

    while session_active:
        try:
            data = client_socket.recv(4096)

            if not data:
                logger.warning(
                    "Client disconnected unexpectedly client=%s user=%s",
                    client_id,
                    session_username or "unknown"
                )
                print(f"Client disconnected unexpectedly: {client_id}")
                break

            buffer += data

            try:
                frames, buffer = extract_frames(buffer)
            except ValueError as error:
                code = str(error)
                logger.warning("Protocol error client=%s error=%s", client_id, code)
                send_response(
                    client_socket,
                    error_response(None, code, protocol_error_message(code))
                )
                buffer = b""
                continue

            for frame in frames:
                request_id = None

                try:
                    message = decode_frame(frame)
                except ValueError as error:
                    code = str(error)
                    logger.warning("Protocol error client=%s error=%s", client_id, code)
                    send_response(
                        client_socket,
                        error_response(None, code, protocol_error_message(code))
                    )
                    continue

                request_id = message.get("request_id")

                valid, error_code, error_message = validate_request(message)

                if not valid:
                    logger.warning(
                        "Validation failed client=%s request_id=%s error=%s",
                        client_id,
                        request_id,
                        error_code
                    )
                    send_response(
                        client_socket,
                        error_response(request_id, error_code, error_message)
                    )
                    continue

                command = message["command"]
                request_id = message["request_id"]
                request_data = message["data"]

                logger.info(
                    "Request client=%s user=%s request_id=%s command=%s",
                    client_id,
                    session_username or "none",
                    request_id,
                    command
                )

                if command == "HELLO":
                    username = request_data["username"].strip()

                    if session_username is not None:
                        send_response(
                            client_socket,
                            error_response(
                                request_id,
                                "INVALID_FIELD",
                                "HELLO has already been completed for this session."
                            )
                        )
                        continue

                    session_username = username

                    send_response(
                        client_socket,
                        success_response(
                            request_id,
                            {
                                "client_id": client_id,
                                "username": session_username,
                                "message": "Welcome to CampusGear Checkout System."
                            }
                        )
                    )

                    logger.info(
                        "HELLO success client=%s user=%s",
                        client_id,
                        session_username
                    )
                    continue

                if session_username is None:
                    logger.warning(
                        "SESSION_REQUIRED client=%s request_id=%s command=%s",
                        client_id,
                        request_id,
                        command
                    )
                    send_response(
                        client_socket,
                        error_response(
                            request_id,
                            "SESSION_REQUIRED",
                            "HELLO must be completed before using this command."
                        )
                    )
                    continue

                if command == "LIST":
                    items = equipment_manager.list_available()
                    send_response(
                        client_socket,
                        success_response(request_id, {"items": items})
                    )
                    logger.info(
                        "LIST success user=%s items=%s",
                        session_username,
                        len(items)
                    )

                elif command == "CHECKOUT":
                    equipment_id = request_data["equipment_id"]
                    success, error_code, message_text, result_data = (
                        equipment_manager.checkout(equipment_id, session_username)
                    )

                    if success:
                        result_data["message"] = message_text
                        response = success_response(request_id, result_data)
                        logger.info(
                            "CHECKOUT success user=%s equipment_id=%s",
                            session_username,
                            equipment_id
                        )
                    else:
                        response = error_response(
                            request_id,
                            error_code,
                            message_text
                        )
                        logger.warning(
                            "CHECKOUT failed user=%s equipment_id=%s error=%s",
                            session_username,
                            equipment_id,
                            error_code
                        )

                    send_response(client_socket, response)

                elif command == "RETURN":
                    equipment_id = request_data["equipment_id"]
                    success, error_code, message_text, result_data = (
                        equipment_manager.return_item(equipment_id, session_username)
                    )

                    if success:
                        result_data["message"] = message_text
                        response = success_response(request_id, result_data)
                        logger.info(
                            "RETURN success user=%s equipment_id=%s",
                            session_username,
                            equipment_id
                        )
                    else:
                        response = error_response(
                            request_id,
                            error_code,
                            message_text
                        )
                        logger.warning(
                            "RETURN failed user=%s equipment_id=%s error=%s",
                            session_username,
                            equipment_id,
                            error_code
                        )

                    send_response(client_socket, response)

                elif command == "MY_ITEMS":
                    items = equipment_manager.get_user_items(session_username)
                    send_response(
                        client_socket,
                        success_response(request_id, {"items": items})
                    )
                    logger.info(
                        "MY_ITEMS success user=%s items=%s",
                        session_username,
                        len(items)
                    )

                elif command == "QUIT":
                    send_response(
                        client_socket,
                        success_response(
                            request_id,
                            {"message": "Session closed gracefully."}
                        )
                    )
                    logger.info(
                        "Client disconnected gracefully client=%s user=%s",
                        client_id,
                        session_username
                    )
                    print(f"Client ended session: {session_username}")
                    session_active = False
                    break

        except ConnectionResetError:
            logger.warning(
                "Connection reset client=%s user=%s",
                client_id,
                session_username or "unknown"
            )
            break

        except OSError as error:
            logger.error("Socket error client=%s error=%s", client_id, error)
            break

    client_socket.close()


def start_server(port):
    equipment_manager = EquipmentManager()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind(("0.0.0.0", port))
        server_socket.listen(1)

        logger.info("Server listening on 0.0.0.0:%s", port)

        print("=" * 48)
        print("        CampusGear Checkout Server")
        print("=" * 48)
        print(f"Server listening on port {port}")
        print("Waiting for a client...")

        client_socket, client_address = server_socket.accept()

        handle_client(
            client_socket,
            client_address,
            equipment_manager
        )

    except OSError as error:
        logger.error("Server error: %s", error)
        print(f"Server error: {error}")

    finally:
        server_socket.close()
        logger.info("Server shutdown complete")
        print("Server stopped.")


def main():
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
    except ValueError:
        print("Error: Port must be an integer.")
        sys.exit(1)

    if port < 1024 or port > 65535:
        print("Error: Port must be between 1024 and 65535.")
        sys.exit(1)

    start_server(port)


if __name__ == "__main__":
    main()
