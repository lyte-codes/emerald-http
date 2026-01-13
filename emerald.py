import socket
from concurrent.futures import ThreadPoolExecutor

class Sender:
    def __init__(self, host: str, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

    def send(self, msg: str):
        self.sock.sendall((msg + "\n").encode("utf-8"))

    def close(self):
        self.sock.close()

class Reciver:
    def __init__(self, host: str, port: int, workers: int = 64):
        self.host = host
        self.port = port
        self.workers = workers

    def handle_client(self, conn, addr):
        print("Connected:", addr)
        buffer = b""

        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break

                buffer += data

                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    print(
                        f"Received '{line.decode('utf-8', errors='replace')}' from {addr}"
                    )
        finally:
            conn.close()
            print("Disconnected:", addr)

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(4096)

        print(f"Listening on {self.host}:{self.port}...")

        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            while True:
                conn, addr = sock.accept()
                pool.submit(self.handle_client, conn, addr)