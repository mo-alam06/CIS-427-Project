import socket
import time

from protocol import PROTOCOL_VERSION, encode_message, MessageReceiver


HOST = "localhost"
PORT = 5050


def make_request(request_id, command, data=None):
    return {
        "version": PROTOCOL_VERSION,
        "type": "request",
        "request_id": request_id,
        "command": command,
        "data": data or {}
    }


def connect_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    return sock


def send_hello(sock, receiver, request_id="test-hello"):
    sock.sendall(
        encode_message(
            make_request(
                request_id,
                "HELLO",
                {"username": "protocol_tester"}
            )
        )
    )
    return receiver.receive_one(sock)


def test_partial_message():
    sock = connect_client()
    receiver = MessageReceiver()

    try:
        send_hello(sock, receiver)

        request = encode_message(
            make_request("partial-1", "LIST")
        )

        split_point = len(request) // 2
        sock.sendall(request[:split_point])
        time.sleep(0.5)
        sock.sendall(request[split_point:])

        response = receiver.receive_one(sock)
        passed = (
            response.get("ok") is True
            and response.get("request_id") == "partial-1"
        )

        print("Partial message:", "PASS" if passed else "FAIL")
    finally:
        sock.close()


def test_multiple_messages():
    sock = connect_client()
    receiver = MessageReceiver()

    try:
        combined = (
            encode_message(
                make_request(
                    "multi-hello",
                    "HELLO",
                    {"username": "protocol_tester"}
                )
            )
            + encode_message(make_request("multi-list", "LIST"))
            + encode_message(make_request("multi-items", "MY_ITEMS"))
        )

        sock.sendall(combined)

        responses = [
            receiver.receive_one(sock),
            receiver.receive_one(sock),
            receiver.receive_one(sock)
        ]

        ids = {r.get("request_id") for r in responses}
        expected = {"multi-hello", "multi-list", "multi-items"}

        print(
            "Multiple messages:",
            "PASS" if ids == expected else "FAIL"
        )
    finally:
        sock.close()


def test_recovery_after_error():
    sock = connect_client()
    receiver = MessageReceiver()

    try:
        send_hello(sock, receiver)

        sock.sendall(
            encode_message(
                make_request("bad-1", "DELETE")
            )
        )
        bad = receiver.receive_one(sock)

        sock.sendall(
            encode_message(
                make_request("good-1", "LIST")
            )
        )
        good = receiver.receive_one(sock)

        passed = (
            bad.get("ok") is False
            and bad.get("error", {}).get("code") == "UNKNOWN_COMMAND"
            and good.get("ok") is True
        )

        print(
            "Recovery after error:",
            "PASS" if passed else "FAIL"
        )
    finally:
        sock.close()


if __name__ == "__main__":
    print("CampusGear Protocol Tests")
    print("Restart server.py before each test because Phase 2 accepts one client.")
    print("Available functions:")
    print("  test_partial_message()")
    print("  test_multiple_messages()")
    print("  test_recovery_after_error()")
