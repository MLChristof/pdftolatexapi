# LaTeX to PDF Compilation API (Enterprise Edition)

A robust, containerized Flask API that converts LaTeX source code into PDF documents. Designed for enterprise deployment with security, observability, and scalability in mind.

## Features

*   **Secure Compilation**: Runs `pdflatex` in a restricted sandbox (via `texmf.cnf`) to prevent file system access and shell execution attacks.
*   **Enterprise Observability**:
    *   **Structured JSON Logging**: Logs are formatted as JSON for easy ingestion by ELK, Splunk, or Datadog.
    *   **Prometheus Metrics**: Exposes a `/metrics` endpoint for monitoring request rates, latency, and errors.
*   **Production-Ready Server**: Uses Gunicorn with a tuned configuration for concurrency (threads + workers).
*   **DoS Protection**: Configurable request size limits and compilation timeouts.
*   **Dockerized**: Fully containerized with a non-root user for enhanced security.

## Prerequisites

*   Docker (or Podman)

## Quick Start

1.  **Build the Docker image:**

    ```bash
    docker build -t pdftolatexapi .
    ```

2.  **Run the container:**

    ```bash
    docker run -p 5000:5000 --name latex-api pdftolatexapi
    ```

3.  **Test the API:**

    ```bash
    # Create a dummy tex file if you don't have one
    echo '\documentclass{article}\begin{document}Hello World\end{document}' > test.tex

    # Compile it
    curl -X POST --data-binary @test.tex http://localhost:5000/compile --output output.pdf
    ```

## Configuration

The application is configured via Environment Variables.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PDFTOLATEX_PORT` | Port the Flask app listens on (internal). | `5000` |
| `MAX_CONTENT_LENGTH` | Max size of the upload in bytes. | `10485760` (10MB) |
| `COMPILATION_TIMEOUT` | Max time (seconds) for `pdflatex` to run. | `30` |

**Example running with custom config:**

```bash
docker run -p 5000:5000 \
  -e COMPILATION_TIMEOUT=60 \
  -e MAX_CONTENT_LENGTH=20971520 \
  pdftolatexapi
```

## API Endpoints

### `POST /compile`
Compiles raw LaTeX content into a PDF.

*   **Body**: Raw `.tex` content (text/plain).
*   **Returns**:
    *   `200 OK`: The compiled PDF file.
    *   `400 Bad Request`: Compilation error (logs provided in JSON response) or missing input.
    *   `408 Request Timeout`: Compilation took too long.
    *   `500 Internal Server Error`: Unexpected server error.

### `GET /health`
Health check endpoint for load balancers and orchestrators.

*   **Returns**: `{"status": "ok", "pdflatex_present": true}`

### `GET /metrics`
Prometheus metrics endpoint.

*   **Returns**: Standard Prometheus metrics (request count, latency, etc.).

### `GET /` or `/apidocs`
Swagger UI documentation.

## Observability

### Logging
Logs are output to `stdout`/`stderr` in JSON format:
```json
{"asctime": "2023-10-27 10:00:00,000", "levelname": "INFO", "name": "root", "message": "PDF compilation succeeded."}
```

### Metrics
The application uses `prometheus-flask-exporter`. Common metrics include:
*   `flask_http_request_duration_seconds_bucket`: Latency distribution.
*   `flask_http_request_total`: Total request count by status and method.

## Development & Testing

### Local Setup
1.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    pip install pytest
    ```
3.  Run the app:
    ```bash
    python app.py
    ```

### Running Tests
Unit and integration tests are located in the `tests/` directory.

```bash
pytest
```
