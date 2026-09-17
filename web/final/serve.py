"""Start the local result website with a valid HTTP origin for map tiles."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial
import argparse,webbrowser,threading
parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);parser.add_argument('--no-browser',action='store_true');args=parser.parse_args()
root=Path(__file__).resolve().parent
class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
        self.send_header('Cache-Control','no-store, no-cache, must-revalidate')
        self.send_header('Pragma','no-cache')
        self.send_header('Expires','0')
        super().end_headers()
server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(root)))
url=f'http://127.0.0.1:{server.server_port}/'
print(url,flush=True)
if not args.no_browser:threading.Timer(.5,lambda:webbrowser.open(url)).start()
try:server.serve_forever()
except KeyboardInterrupt:server.server_close()
