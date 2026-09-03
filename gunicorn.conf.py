"""Gunicorn config. Run with:  gunicorn -c gunicorn.conf.py config.wsgi:application"""

import multiprocessing
import os

# Listen on a TCP port by default; set GUNICORN_BIND to a
# "unix:/run/grd-backend/gunicorn.sock" path if something proxies it instead.
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

workers = int(os.getenv("GUNICORN_WORKERS", str(multiprocessing.cpu_count() * 2 + 1)))
worker_class = "sync"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))

# Recycle workers periodically to bound memory growth.
max_requests = 1000
max_requests_jitter = 100

accesslog = "-"   # -> journald via systemd
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")
