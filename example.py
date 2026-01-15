import sys, time, datetime
import emerald

try:
    server = emerald.HTTPServer(sys.argv[1], int(sys.argv[2]))
except:
    print("Usage: python3 example.py <hostname> <port>")
    exit(1)

@server.route("GET", "/api")
def api():
    return f"{time.time()}\n"

@server.route("GET", "/")
def human():
    today = datetime.date.today()
    now = datetime.datetime.now()
    
    return emerald.Template("./template.html").fill(
        day    = str(today.strftime("%A")),
        daynum = str(today.day),
        month  = str(now.strftime("%B")),
        year   = str(today.year),
        hour   = str(now.strftime("%I")),
        minute = str(now.minute).ljust(2, "0"),
        second = str(now.second).ljust(2, "0"),
        ampm   = str(now.strftime("%p"))
    )

server.run()