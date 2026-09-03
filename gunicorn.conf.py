"""Gunicorn config. Run with:  gunicorn -c gunicorn.conf.py config.wsgi:application"""

import multiprocessing
import os

# Bind to a Unix socket by default (nginx talks to it); override with GUNICORN_BIND
# e.g. GUNICORN_BIND=0.0.0.0:8000 to expose it directly.
bind = os.getenv("GUNICORN_BIND", "unix:/run/grd-backend/gunicorn.sock")

workers = int(os.getenv("GUNICORN_WORKERS", str(multiprocessing.cpu_count() * 2 + 1)))
worker_class = "sync"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))

# Recycle workers periodically to bound memory growth.
max_requests = 1000
max_requests_jitter = 100

accesslog = "-"   # -> journald via systemd
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")
