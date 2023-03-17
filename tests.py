import unittest
import asyncio
from rpc_websocket import RPCWebSocket
from rich.console import Console

console = Console()


class TestRPCWebSocket(unittest.IsolatedAsyncioTestCase):
    async def test_local_method_registration_and_call(self):
        try:
            console.print("🚀 [bold green]Starting server...")
            server = RPCWebSocket("server", "localhost", 9000)

            def local_method(arg1, arg2):
                return arg1 * arg2

            server.register_local_method(local_method)
            server_task = asyncio.create_task(server.start())

            console.print("🚀 [bold green]Starting client...")
            client = RPCWebSocket(
                "client", "localhost", 9000, reconnect_interval=1, timeout=2
            )
            client_task = asyncio.create_task(client.start())

            await asyncio.sleep(
                1
            )  # Add a small delay to allow WebSocket connections to establish

            console.print("🔍 [bold yellow]Sending RPC request...")
            with console.status("[bold yellow]Processing RPC request..."):
                result = await client.send_rpc_request("local_method", 5, 6)

            console.print("🎯 [bold cyan]Result: ", result)
            self.assertEqual(result, 30)

        except Exception as e:
            console.print_exception()
        finally:
            console.print("🛑 [bold green]Stopping server and client...")
            await server.stop()
            await client.stop()
            server_task.cancel()
            client_task.cancel()

    async def test_error_handling(self):
        try:
            console.print("🚀 [bold green]Starting server...")
            server = RPCWebSocket("server", "localhost", 9002)

            def error_method(arg1, arg2):
                raise ValueError("An error occurred")

            server.register_local_method(error_method)
            server_task = asyncio.create_task(server.start())

            console.print("🚀 [bold green]Starting client...")
            client = RPCWebSocket(
                "client", "localhost", 9002, reconnect_interval=1, timeout=2
            )
            client_task = asyncio.create_task(client.start())

            await asyncio.sleep(
                1
            )  # Add a small delay to allow WebSocket connections to establish

            console.print("🔍 [bold yellow]Sending RPC request with error method...")
            with console.status(
                "[bold yellow]Processing RPC request with error method..."
            ):
                try:
                    result = await client.send_rpc_request("error_method", 5, 6)
                except Exception as e:
                    # console.print("❌ [bold red]Error: ", str(e))
                    self.assertEqual(str(e), "An error occurred")
                else:
                    self.fail("Expected exception not raised")

        except Exception as e:
            console.print_exception()
        finally:
            console.print("🛑 [bold green]Stopping server and client...")
            await server.stop()
            await client.stop()
            server_task.cancel()
            client_task.cancel()

    async def test_timeout(self):
        try:
            console.print("🚀 [bold green]Starting server with slow method...")
            server = RPCWebSocket("server", "localhost", 9001)

            async def slow_method(arg1, arg2):
                await asyncio.sleep(2)
                return arg1 + arg2

            server.register_local_method(slow_method)
            server_task = asyncio.create_task(server.start())

            console.print("🚀 [bold green]Starting client...")
            client = RPCWebSocket(
                "client", "localhost", 9001, reconnect_interval=1, timeout=1
            )
            client_task = asyncio.create_task(client.start())

            await asyncio.sleep(
                1
            )  # Add a small delay to allow WebSocket connections to establish

            console.print("🔍 [bold yellow]Sending RPC request with timeout...")
            with self.assertRaises(Exception):
                result = await client.send_rpc_request("slow_method", 5, 6)
            console.print("⏰ [bold green]Timeout occurred")

        except Exception as e:
            console.print_exception()
        finally:
            console.print("🛑 [bold green]Stopping server and client...")
            await server.stop()
            await client.stop()
            server_task.cancel()
            client_task.cancel()
