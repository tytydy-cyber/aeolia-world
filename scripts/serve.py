import functools
import http.server
import os

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")
http.server.test(HandlerClass=functools.partial(http.server.SimpleHTTPRequestHandler, directory=root), port=8794, bind="127.0.0.1")
