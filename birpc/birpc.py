import os
import asyncio
import json
import uuid
import logging
from aiohttp import ClientSession, WSMsgType, ClientConnectorError, web
from rich.logging import RichHandler
from rich.console import Console
import traceback

# Set up the logging configuration
LOG_LEVEL = logging.DEBUG if "DEBUG" in os.environ else logging.INFO

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)

logger = logging.getLogger("rpc_websocket")


class RPCWebSocket:
    def __init__(self, mode, host, port, reconnect_interval=None, timeout=None):
        self.mode = mode
        self.host = host
        self.port = port
        self.reconnect_interval = reconnect_interval
        self.timeout = timeout
        self.ws = None
        self.pending_requests = {}
        self.local_methods = {}

    def register_local_method(self, method):
        self.local_methods[method.__name__] = method
        logger.info(f"📌 Registered local method: {method.__name__}")

    async def start(self):
        if self.mode == "client":
            await self.start_client()
        elif self.mode == "server":
            await self.start_server()
        else:
            raise ValueError("Invalid mode")

    async def start_client(self):
        logger.info(f"🚀 Starting client on {self.host}:{self.port}")
        async with ClientSession() as session:
            while True:
                try:
                    async with session.ws_connect(
                        f"ws://{self.host}:{self.port}"
                    ) as ws:
                        self.ws = ws
                        await self.handle_messages()
                except ClientConnectorError:
                    logger.warning(
                        f"⚠️ Connection failed. Retrying in {self.reconnect_interval} seconds..."
                    )
                    await asyncio.sleep(self.reconnect_interval)

    async def start_server(self):
        logger.info(f"🚀 Starting server on {self.host}:{self.port}")
        app = web.Application()
        app.router.add_route("GET", "/", self.websocket_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        self.server_task = asyncio.create_task(site.start())
        self.stop_event = asyncio.Event()
        await self.stop_event.wait()

    async def stop(self):
        logger.info("🛑 Stopping...")
        if self.mode == "client":
            if self.ws is not None:
                await self.ws.close()
        elif self.mode == "server":
            if self.ws is not None:
                await self.ws.close()
            if hasattr(self, "site") and self.site is not None:
                await self.site.stop()
            if hasattr(self, "runner") and self.runner is not None:
                await self.runner.cleanup()
            self.stop_event.set()

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse(protocols=["json"])
        await ws.prepare(request)
        self.ws = ws
        await self.handle_messages()
        return ws

    async def handle_messages(self):
        async for msg in self.ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)
                if data["t"] == "q":
                    await self.handle_rpc_request(data)
                elif data["t"] == "s":
                    future = self.pending_requests.pop(data["i"], None)
                    if future:
                        if "e" in data:
                            logger.warning(
                                f"❌ Error from RPC response for uid: {data['i']}, error: {data['e']}"
                            )
                            future.set_exception(Exception(data["e"]["message"]))
                        else:
                            future.set_result(data["r"])

    async def handle_rpc_request(self, request):
        method_name = request["m"]
        args = request["a"]
        uid = request["i"]

        if method_name in self.local_methods:
            method = self.local_methods[method_name]
            logger.info(
                f"🔍 Processing RPC request for method: {method_name}, args: {args}, uid: {uid}"
            )
            try:
                if asyncio.iscoroutinefunction(method):
                    result = await method(*args)
                else:
                    result = method(*args)

                response = {"t": "s", "i": uid, "r": result}
            except Exception as e:
                response = {"t": "s", "i": uid, "e": {"message": str(e)}}
                result = None
                logger.warning(
                    f"❌ Error processing RPC request for uid: {uid}, error: {str(e)}"
                )

                tb_str = traceback.format_exception(
                    etype=type(e), value=e, tb=e.__traceback__
                )
                logger.debug(
                    f"❌ Detailed error processing RPC request for uid: {uid}, error: {str(e)}\n{''.join(tb_str)}"
                )

            await self.ws.send_str(json.dumps(response))
            logger.info(f"📤 Sent RPC response for uid: {uid}, result: {result}")
        else:
            logger.warning(f"⚠️ Unknown method requested: {method_name}")

    async def call(self, method, *args):
        uid = str(uuid.uuid4())[:16]
        request = {"m": method, "a": args, "i": uid, "t": "q"}
        logger.info(
            f"📥 Sending RPC request for method: {method}, args: {args}, uid: {uid}"
        )
        await self.ws.send_str(json.dumps(request))
        future = asyncio.Future()
        self.pending_requests[uid] = future
        try:
            result = await asyncio.wait_for(future, self.timeout)
            logger.info(f"🎯 Received RPC response for uid: {uid}, result: {result}")
            return result
        except asyncio.TimeoutError:
            self.pending_requests.pop(uid, None)
            logger.warning(f"⏰ Timeout for RPC request with uid: {uid}")
            raise Exception(f"Timeout")


if __name__ == "__main__":
    rpc = RPCWebSocket("server", "127.0.0.1", 11111)

    def local_method(arg1, arg2):
        return arg1 + arg2

    rpc.register_local_method(local_method)
    try:
        asyncio.run(rpc.start())
        while True:
            asyncio.run(asyncio.sleep(1))
    except KeyboardInterrupt:
        logger.info("🛑 Stopping...")
        asyncio.run(rpc.stop())
