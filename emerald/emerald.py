"""
Emerald HTTP Server 2.2
"""

import socket
from concurrent.futures import ThreadPoolExecutor
import os
import html
import traceback

class ErrorPages:
    def __init__(
        self,
        directory: str = "errors",
        dev_mode: bool = False
    ):
        self.directory = directory
        self.dev_mode = dev_mode

    def _load(self, code: int):
        path = os.path.join(self.directory, f"{code}.html")
        if not os.path.isfile(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def render(
        self,
        code: int,
        *,
        path: str = "",
        method: str = "",
        error: Exception | None = None
    ) -> tuple[str, str]:
        """
        Returns (body, content_type)
        """

        template = self._load(code)

        # ---------- Plain text fallback ----------
        if template is None:
            body = f"{code} Error\n"
            if self.dev_mode and error:
                body += str(error) + "\n"
            return body, "text/plain"

        # ---------- Template variables ----------
        vars = {
            "code": code,
            "path": html.escape(path),
            "method": method,
        }

        if self.dev_mode and error:
            vars["error"] = html.escape(str(error))
            vars["traceback"] = html.escape(
                "".join(traceback.format_exception(error))
            )
        else:
            vars["error"] = ""
            vars["traceback"] = ""

        try:
            return template.format(**vars), "text/html"
        except Exception:
            # Template formatting failure
            return f"{code} Error\n", "text/plain"
        
class HTTPServer:
    def __init__(self, host: str, port: int, workers: int = 64, errors: ErrorPages = ErrorPages()):
        self.host = host
        self.port = port
        self.workers = workers
        self.router = Router()
        self.errors = errors

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
                body = self.errors.render(404)[0].encode("utf-8")
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