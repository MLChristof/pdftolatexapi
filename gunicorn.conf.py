import multiprocessing
import os

# Gunicorn configuration file
bind = "0.0.0.0:5000"

# Worker configuration
# Rule of thumb: 2 * CPU + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"  # Use threads for better concurrency with I/O bound tasks
threads = 4
timeout = 120  # Longer timeout for LaTeX compilation
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "pdftolatexapi"

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
