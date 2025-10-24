# Start from a slim Python base image
FROM python:3.11-slim

# Install TeX Live essentials.
# apt-get -yqq means quiet and assume yes.
RUN apt-get update && apt-get install -yqq --no-install-recommends \
    texlive-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-lang-recommended \
    texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

# Set up the application directory
WORKDIR /app

# Copy the security configuration into the system-wide TeX config directory
COPY texmf.cnf /etc/texmf/web2c/texmf.cnf

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our Flask application code into the container
COPY app.py .

# Create and switch to a non-root user for better security
RUN addgroup --system appuser && adduser --system --group appuser
USER appuser

# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]