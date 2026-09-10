import socket
import sys

from protocol import PROTOCOL_VERSION, encode_message, MessageReceiver


class RequestIdGenerator:
    def __init__(self):
        self.counter = 0

    def next_id(self):
        self.counter += 1
        return f"r{self.counter}"


def build_request(request_id, command, data=None):
    return {
        "version": PROTOCOL_VERSION,
        "type": "request",
        "request_id": request_id,
        "command": command,
        "data": data or {}
    }


def send_request(client_socket, request):
    client_socket.sendall(encode_message(request))


def display_error(response):
    error = response.get("error", {})
    code = error.get("code", "UNKNOWN_ERROR")
    message = error.get("message", "An unknown error occurred.")
    print(f"\nError [{code}]: {message}")


def display_items(items):
    print()

    if not items:
        print("No equipment found.")
        return

    print(f"{'ID':<8}{'Name':<25}{'Category':<18}{'Status':<15}")
    print("-" * 66)

    for item in items:
        print(
            f"{item['id']:<8}"
            f"{item['name']:<25}"
            f"{item['category']:<18}"
            f"{item['status']:<15}"
        )


def get_username():
    while True:
        username = input("Enter your username: ").strip()

        if not username:
            print("Username cannot be empty.")
            continue

        if len(username) > 50:
            print("Username must be 50 characters or fewer.")
            continue

        return username


def get_equipment_id():
    while True:
        value = input("Enter equipment ID: ").strip()

        if not value:
            print("Equipment ID cannot be empty.")
            continue

        try:
            equipment_id = int(value)
        except ValueError:
            print("Equipment ID must be a number.")
            continue

        if equipment_id <= 0:
            print("Equipment ID must be greater than zero.")
            continue

        return equipment_id


def show_menu():
    print()
    print("=" * 48)
    print("       CampusGear Checkout System")
    print("=" * 48)
    print("1. View available equipment")
    print("2. Checkout equipment")
    print("3. Return equipment")
    print("4. View my equipment")
    print("5. Exit")
    print("=" * 48)


def receive_matching_response(receiver, client_socket, expected_request_id):
    while True:
        response = receiver.receive_one(client_socket)

        if response.get("request_id") == expected_request_id:
            return response

        print(
            "Warning: Received response for unexpected "
            f"request_id={response.get('request_id')}"
        )


def perform_request(
    client_socket,
    receiver,
    id_generator,
    command,
    data=None
):
    request_id = id_generator.next_id()
    request = build_request(request_id, command, data)
    send_request(client_socket, request)

    return receive_matching_response(
        receiver,
        client_socket,
        request_id
    )


def start_session(client_socket, receiver, id_generator, username):
    response = perform_request(
        client_socket,
        receiver,
        id_generator,
        "HELLO",
        {"username": username}
    )

    if not response.get("ok", False):
        display_error(response)
        return False

    data = response.get("data", {})
    print("\n" + data.get("message", "Session started."))
    print(f"Logged in as: {username}")
    return True


def handle_list(client_socket, receiver, id_generator):
    response = perform_request(
        client_socket,
        receiver,
        id_generator,
        "LIST"
    )

    if not response.get("ok", False):
        display_error(response)
        return

    items = response.get("data", {}).get("items", [])
    print("\nAvailable Equipment")
    display_items(items)


def handle_checkout(client_socket, receiver, id_generator):
    equipment_id = get_equipment_id()

    response = perform_request(
        client_socket,
        receiver,
        id_generator,
        "CHECKOUT",
        {"equipment_id": equipment_id}
    )

    if not response.get("ok", False):
        display_error(response)
        return

    print(
        "\nSuccess:",
        response.get("data", {}).get(
            "message",
            "Equipment checked out successfully."
        )
    )


def handle_return(client_socket, receiver, id_generator):
    equipment_id = get_equipment_id()

    response = perform_request(
        client_socket,
        receiver,
        id_generator,
        "RETURN",
        {"equipment_id": equipment_id}
    )

    if not response.get("ok", False):
        display_error(response)
        return

    print(
        "\nSuccess:",
        response.get("data", {}).get(
            "message",
            "Equipment returned successfully."
        )
    )


def handle_my_items(client_socket, receiver, id_generator):
    response = perform_request(
        client_socket,
        receiver,
        id_generator,
        "MY_ITEMS"
    )

    if not response.get("ok", False):
        display_error(response)
        return

    items = response.get("data", {}).get("items", [])
    print("\nMy Equipment")
    display_items(items)


def handle_quit(client_socket, receiver, id_generator):
    response = perform_request(
        client_socket,
        receiver,
        id_generator,
        "QUIT"
    )

    if not response.get("ok", False):
        display_error(response)
        return False

    print(
        "\n" + response.get("data", {}).get(
            "message",
            "Session closed."
        )
    )
    return True


def start_client(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    receiver = MessageReceiver()
    id_generator = RequestIdGenerator()

    try:
        print(f"Connecting to {host}:{port}...")
        client_socket.connect((host, port))
        print("Connected to CampusGear Server.")

        username = get_username()

        if not start_session(
            client_socket,
            receiver,
            id_generator,
            username
        ):
            return

        running = True

        while running:
            show_menu()
            choice = input("Select an option: ").strip()

            if choice == "1":
                handle_list(client_socket, receiver, id_generator)
            elif choice == "2":
                handle_checkout(client_socket, receiver, id_generator)
            elif choice == "3":
                handle_return(client_socket, receiver, id_generator)
            elif choice == "4":
                handle_my_items(client_socket, receiver, id_generator)
            elif choice == "5":
                running = not handle_quit(
                    client_socket,
                    receiver,
                    id_generator
                )
            else:
                print("Invalid choice. Please select 1 through 5.")

    except ConnectionRefusedError:
        print("\nError: Could not connect to the server.")
        print("Make sure the server is running and the port is correct.")
    except socket.gaierror:
        print("\nError: Invalid hostname.")
    except ConnectionError as error:
        print(f"\nConnection error: {error}")
    except KeyboardInterrupt:
        print("\nClient interrupted by user.")
    except OSError as error:
        print(f"\nNetwork error: {error}")
    finally:
        client_socket.close()
        print("Client connection closed.")


def main():
    if len(sys.argv) != 3:
        print("Usage: python client.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]

    try:
        port = int(sys.argv[2])
    except ValueError:
        print("Error: Port must be an integer.")
        sys.exit(1)

    if port < 1024 or port > 65535:
        print("Error: Port must be between 1024 and 65535.")
        sys.exit(1)

    start_client(host, port)


if __name__ == "__main__":
    main()
