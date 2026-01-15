import sys, time, datetime
import emerald

try:
    server = emerald.HTTPServer(sys.argv[1], int(sys.argv[2]), 64, emerald.ErrorPages("example-error-pages"))
except:
    print("Usage: python3 example.py <hostname> <port>")
    exit(1)
    
@server.route("GET", "/api")
def api(request):
    return f"{time.time()}\n"

@server.route("GET", "/")
def human(request):
    today = datetime.date.today()
    now = datetime.datetime.now()
    
    return emerald.Template("./example.html").fill(
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