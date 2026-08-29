import asyncio

async def stream(messages):
    while True:
        message = await messages.get()
        yield message
        if message[0] == 0 or message[0] == 2:
            break

def notify(code: int, data: bytes, messages: asyncio.Queue):
    """The worker already serializes the result into the final wire format
    before sending it (see manga_translator/mode/share.py); just re-frame it."""
    encoded_result = code.to_bytes(1, 'big') + len(data).to_bytes(4, 'big') + data
    messages.put_nowait(encoded_result)
