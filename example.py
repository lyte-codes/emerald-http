import emerald, sys

try:
    server = emerald.HTTPServer(sys.argv[1], int(sys.argv[2]))
except:
    print("Usage: python3 example.py <hostname> <port>")
    exit(1)

@server.route("GET", "/api")
def api():
    import time
    return f"{time.time()}\n"

@server.route("GET", "/")
def about():
    return f"""
        <h1>Emerald 2.0 Test</h1>
        <p>This time API is a test of Emerald HTTP Server v2.0. Go to /api to get the time.</p>
    """

server.run()