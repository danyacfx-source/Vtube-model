"""Offline, loopback-only web server for the live-camera fruit app."""
import argparse, functools, http.server, pathlib, threading, webbrowser
parser=argparse.ArgumentParser()
parser.add_argument('--port',type=int,default=8765)
parser.add_argument('--no-browser',action='store_true')
args=parser.parse_args()
class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,'.js':'application/javascript','.wasm':'application/wasm','.vrm':'model/gltf-binary'}
    def end_headers(self):
        self.send_header('Cache-Control','no-cache')
        super().end_headers()
root=pathlib.Path(__file__).resolve().parent
try: server=http.server.ThreadingHTTPServer(('127.0.0.1',args.port),functools.partial(Handler,directory=str(root)))
except OSError as error:
    raise SystemExit(f'Cannot start local server on port {args.port}: {error}. Close the previous app or use --port 8766.')
url=f'http://127.0.0.1:{args.port}/'
print(f'Live fruit app: {url}\nKeep this window open. Press Ctrl+C to stop.',flush=True)
if not args.no_browser:threading.Timer(.6,lambda:webbrowser.open(url)).start()
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
