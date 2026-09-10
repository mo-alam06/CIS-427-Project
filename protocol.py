import json

PROTOCOL_VERSION = "1.0"
ENCODING = "utf-8"
DELIMITER = b"\n"
MAX_MESSAGE_SIZE = 8192


def encode_message(message):
    if not isinstance(message, dict):
        raise ValueError("INVALID_MESSAGE")

    try:
        payload = json.dumps(
            message,
            separators=(",", ":"),
            ensure_ascii=False
        ).encode(ENCODING)
    except (TypeError, ValueError):
        raise ValueError("INVALID_MESSAGE")

    if len(payload) > MAX_MESSAGE_SIZE:
        raise ValueError("MESSAGE_TOO_LARGE")

    return payload + DELIMITER


def extract_frames(buffer):
    frames = []

    while DELIMITER in buffer:
        frame, buffer = buffer.split(DELIMITER, 1)
        frames.append(frame)

    if len(buffer) > MAX_MESSAGE_SIZE:
        raise ValueError("MESSAGE_TOO_LARGE")

    return frames, buffer


def decode_frame(frame):
    if not frame:
        raise ValueError("EMPTY_MESSAGE")

    if len(frame) > MAX_MESSAGE_SIZE:
        raise ValueError("MESSAGE_TOO_LARGE")

    try:
        text = frame.decode(ENCODING)
    except UnicodeDecodeError:
        raise ValueError("INVALID_MESSAGE")

    try:
        message = json.loads(text)
    except json.JSONDecodeError:
        raise ValueError("MALFORMED_JSON")

    if not isinstance(message, dict):
        raise ValueError("INVALID_MESSAGE")

    return message


class MessageReceiver:
    def __init__(self):
        self.buffer = b""
        self.pending = []

    def receive_one(self, sock):
        while not self.pending:
            data = sock.recv(4096)

            if not data:
                raise ConnectionError("Remote endpoint disconnected.")

            self.buffer += data
            frames, self.buffer = extract_frames(self.buffer)

            for frame in frames:
                self.pending.append(decode_frame(frame))

        return self.pending.pop(0)
