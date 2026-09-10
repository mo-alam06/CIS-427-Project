# CampusGear Equipment Checkout System
## CIS 427 – Socket Programming Project

**Team Members:** Abdulrazzaq Shewia, Mohammed Alam  
**Instructor:** Jinhua Guo

CampusGear is a TCP client-server equipment checkout system implemented
with Python standard-library modules.

## Files

- `server.py` – TCP server and request processing
- `client.py` – menu-based command-line client
- `protocol.py` – JSON encoding, newline framing, message buffering
- `validation.py` – request validation
- `equipment.py` – server-side equipment state and business logic
- `protocol_test_client.py` – framing and recovery tests
- `server.log` – generated server log

## Run

Terminal 1:

```bash
python server.py 5050
```

Terminal 2:

```bash
python client.py localhost 5050
```

Then enter a username and use:

1. View available equipment
2. Checkout equipment
3. Return equipment
4. View my equipment
5. Exit

## Protocol

Messages use UTF-8 JSON with newline (`\n`) framing.

Example:

```json
{
  "version": "1.0",
  "type": "request",
  "request_id": "r1",
  "command": "LIST",
  "data": {}
}
```

Supported commands:

- HELLO
- LIST
- CHECKOUT
- RETURN
- MY_ITEMS
- QUIT

The server owns the equipment state. Phase 2 supports one active client.
