"""
Emerald HTTP Server 2.0
"""

import socket
from concurrent.futures import ThreadPoolExecutor

class HTTPServer:
    def __init__(self, host: str, port: int, workers: int = 64):
        self.host = host
        self.port = port
        self.workers = workers
        self.router = Router()

    def route(self, method: str, path: str):
        def decorator(fn):
            self.router.add(method, path, fn)
            return fn
        return decorator

    def handle_client(self, conn, addr):
        try:
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(4096)
                if not chunk:
                    return
                data += chunk

            request = data.decode("utf-8", errors="replace")
            request_line = request.split("\r\n", 1)[0]
            method, path, _ = request_line.split(" ", 2)

            handler, params = self.router.match(method, path)

            if handler is None:
                body = b"404 Not Found\n"
                response = (
                    "HTTP/1.1 404 Not Found\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    "Connection: close\r\n\r\n"
                ).encode() + body
            else:
                body = handler(params)
                body = body.encode() if isinstance(body, str) else body
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/html; charset=utf-8\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    "Connection: close\r\n\r\n"
                ).encode() + body

            conn.sendall(response)

        except Exception as e:
            print("Error:", e)
        finally:
            conn.close()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(4096)

        print(f"Listening on {self.host}:{self.port}")

        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            while True:
                conn, addr = sock.accept()
                pool.submit(self.handle_client, conn, addr)

class Router:
    def __init__(self):
        self.routes = []

    def add(self, method: str, path: str, handler):
        parts = path.strip("/").split("/")
        self.routes.append((method, parts, handler))

    def match(self, method: str, path: str):
        path_parts = path.strip("/").split("/")

        for m, route_parts, handler in self.routes:
            if m != method:
                continue
            if len(route_parts) != len(path_parts):
                continue

            params = {}
            matched = True

            for rp, pp in zip(route_parts, path_parts):
                if rp.startswith("<") and rp.endswith(">"):
                    params[rp[1:-1]] = pp
                elif rp != pp:
                    matched = False
                    break

            if matched:
                return handler, params

        return None, None
    
class Template:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def fill(self, **kwargs) -> str:
        with open(self.filepath, "r", encoding="utf-8") as f:
            return f.read().format(**kwargs)