import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
timeout = 120
keepalive = 2

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Debugging
debug = False
reload = False

# Logging
log_level = "info"
accesslog = "/var/log/ep-simulator/access.log"
errorlog = "/var/log/ep-simulator/error.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

# Process naming
proc_name = "ep-simulator"

# Server hooks
def on_starting(server):
    server.log.info("Starting EP-Simulator server...")

def on_reload(server):
    server.log.info("Reloading EP-Simulator server...")

def when_ready(server):
    server.log.info("EP-Simulator server is ready.")

def on_exit(server):
    server.log.info("EP-Simulator server is shutting down...")

def worker_int(worker):
    worker.log.info("Worker received INT or QUIT signal")

    # Get traceback info
    import threading, sys, traceback
    id2name = {th.ident: th.name for th in threading.enumerate()}
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(threadId, ""), threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                code.append('  %s' % (line.strip()))
    worker.log.debug("\n".join(code))

def worker_abort(worker):
    worker.log.warning("Worker received SIGABRT signal")
