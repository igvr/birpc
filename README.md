# 🔄 BIRPC

BIRPC is a simple and efficient bidirectional RPC (Remote Procedure Call) library built on top of WebSockets for Python. It facilitates seamless communication between server and client applications using the power of asynchronous Python. BIRPC is inspired by and a Python version of the original JavaScript package [biRPC](https://www.npmjs.com/package/birpc).

## 🌟 Features

- 🔄 Bidirectional communication between server and client
- 🚀 Asynchronous support with `asyncio`
- 🛡️ Flexible error handling and timeouts
- 📌 Simple method registration and remote invocation
- ⚡ Built on top of WebSockets for efficient communication

## ⚙️ Installation

```bash
pip install birpc
```

## 🛠️ Usage

### Server

```python
import asyncio
from birpc import BIRPC

async def main():
    server = BIRPC("server", "localhost", 9000)

    def local_method(arg1, arg2):
        return arg1 * arg2

    server.register_local_method(local_method)

    await server.start()

asyncio.run(main())
```

### Client

```python
import asyncio
from birpc import BIRPC

async def main():
    client = BIRPC("client", "localhost", 9000, reconnect_interval=1, timeout=2)

    await client.start()

    result = await client.send_rpc_request("local_method", 5, 6)
    print("Result:", result)

asyncio.run(main())
```

## 🔧 Error Handling

BIRPC has built-in error handling, which allows you to capture and process exceptions raised by remote methods.

### Example

```python
import asyncio
from birpc import BIRPC

async def main():
    client = BIRPC("client", "localhost", 9000, reconnect_interval=1, timeout=2)

    await client.start()

    try:
        result = await client.send_rpc_request("local_method", 5, 6)
        print("Result:", result)
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
```

## ⏲️ Timeout

Timeouts can be specified during client initialization, ensuring that RPC requests don't hang indefinitely.

## 📄 License

This project is licensed under the MIT License.

## 🙌 Acknowledgements

This module was fully written by ChatGPT-4, by OpenAI. 🤖💬