import asyncio
import websockets
import json

class WebsocketClient:
    def __init__(self, sender_id, url='ws://localhost:8766'):
        self.sender_id = sender_id
        self.url = url
        self.websocket = None

    async def connect(self):
        """Connect to the websocket server"""
        self.websocket = await websockets.connect(self.url)
        await self.websocket.send(json.dumps({
            'action': 'register',
            'sender_id': self.sender_id
        }))
        print(f"Connected to websocket server as sender_id: {self.sender_id}")

    async def listen(self):
        """Listen for incoming messages"""
        try:
            async for message in self.websocket:
                task = json.loads(message)
                print(f"New task received: {task}")
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")

    async def run(self):
        """Run the client"""
        await self.connect()
        await self.listen()