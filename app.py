"""
LaTeX to PDF Compilation API

Enterprise-grade Flask app for compiling LaTeX source to PDF with security scanning, logging, and health checks.
Follows Python best practices and is ready for Azure deployment.
"""

import logging
from typing import Any
import os
import subprocess
import tempfile
from flask import Flask, request, send_file, jsonify
from flasgger import Swagger
from pythonjsonlogger import jsonlogger
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

# Enterprise Configuration
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 10 * 1024 * 1024)) # 10MB default
COMPILATION_TIMEOUT = int(os.getenv('COMPILATION_TIMEOUT', 30))

# Configure logging for enterprise monitoring (JSON format)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s'
)
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Initialize Prometheus metrics
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')

# Swagger configuration template (minimal). Adjust versions/info as needed.
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "LaTeX to PDF Compilation API",
        "description": "Compile raw LaTeX source (.tex) to PDF securely. Security scanning blocks dangerous commands.",
        "version": "1.0.0"
    },
    "schemes": ["http"],
    "basePath": "/",
    "tags": [
        {"name": "compile", "description": "Compilation operations"},
        {"name": "system", "description": "System/health endpoints"}
    ]
}

swagger = Swagger(app, template=swagger_template)

# Root route for API documentation
@app.route('/')
def api_docs() -> tuple[str, int, dict]:
    """
    Landing page.
    ---
    get:
        tags:
            - system
        summary: Simple HTML landing page
        description: Returns a human-readable HTML page with basic usage info. For interactive API docs visit /apidocs.
        produces:
            - text/html
        responses:
            200:
                description: HTML documentation page
    """
    doc_html = '''<html>
    <head><title>LaTeX to PDF API</title></head>
    <body>
        <h1>LaTeX to PDF API</h1>
        <p>Interactive Swagger UI: <a href="/apidocs">/apidocs</a></p>
        <h2>Quick example</h2>
        <pre>curl -X POST --data-binary @testfile.tex http://localhost:5000/compile --output output.pdf</pre>
    </body>
    </html>'''
    return doc_html, 200, {'Content-Type': 'text/html'}

@app.route('/compile', methods=['POST'])
def compile_tex() -> Any:
    """
    Compile LaTeX source to PDF.
    ---
    post:
      tags:
        - compile
      summary: Compile LaTeX (.tex) content into a PDF
      consumes:
        - text/plain
      produces:
        - application/pdf
        - application/json
      parameters:
        - in: body
          name: body
          description: Raw LaTeX source (.tex) content
          required: true
          schema:
            type: string
      responses:
        200:
          description: Successfully compiled PDF.
        400:
          description: Compilation failed or bad input.
        403:
          description: Security check failed (dangerous command detected).
        408:
          description: Compilation timed out.
        500:
          description: Internal server error.
    """
    tex_content = request.get_data(as_text=True)
    if not tex_content:
        logger.warning("No .tex content provided in the request body.")
        return jsonify({"error": "No .tex content provided in the request body."}), 400

    # Compile using a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_filename = "document.tex"
        pdf_filename = "document.pdf"
        log_filename = "document.log"

        # Write the file to the temporary directory
        tex_filepath = os.path.join(temp_dir, tex_filename)
        with open(tex_filepath, 'w') as f:
            f.write(tex_content)

        # Run pdflatex with restricted shell escape (default in most distros, enforced by texmf.cnf)
        # We set cwd to temp_dir to contain relative file paths.
        command = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-output-directory=.", # Output to current working directory (temp_dir)
            tex_filename
        ]

        try:
            proc = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=COMPILATION_TIMEOUT,
                cwd=temp_dir # Set working directory to the temp folder
            )

            if proc.returncode != 0:
                log_filepath = os.path.join(temp_dir, log_filename)
                log_content = ""
                if os.path.exists(log_filepath):
                    with open(log_filepath, 'r') as log_file:
                        log_content = log_file.read()
                logger.error("PDF compilation failed.", extra={"stdout": proc.stdout, "stderr": proc.stderr})
                return jsonify({
                    "error": "PDF compilation failed.",
                    "logs": log_content
                }), 400

            logger.info("PDF compilation succeeded.")
            pdf_filepath = os.path.join(temp_dir, pdf_filename)
            return send_file(
                pdf_filepath,
                as_attachment=True,
                download_name='output.pdf',
                mimetype='application/pdf'
            )

        except subprocess.TimeoutExpired:
            logger.error(f"Compilation timed out after {COMPILATION_TIMEOUT} seconds.")
            return jsonify({"error": f"Compilation timed out after {COMPILATION_TIMEOUT} seconds."}), 408
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
            return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health() -> Any:
    """
    Health check.
    ---
    get:
        tags:
            - system
        summary: Health check endpoint
        description: Returns basic service health information.
        produces:
            - application/json
        responses:
            200:
                description: Service is healthy.
    """
    from shutil import which
    status = {
        "status": "ok",
        "pdflatex_present": which("pdflatex") is not None
    }
    logger.info(f"Health check: {status}")
    return jsonify(status), 200

if __name__ == '__main__':
    port = int(os.getenv("PDFTOLATEX_PORT", "5000"))
    logger.info(f"Starting app on port {port}")
    app.run(host='0.0.0.0', port=port)