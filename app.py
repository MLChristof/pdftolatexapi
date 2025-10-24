import os
import subprocess
import tempfile
from flask import Flask, request, send_file, jsonify

# Initialize the Flask application
app = Flask(__name__)

@app.route('/compile', methods=['POST'])
def compile_tex():
    """
    Compiles TeX content received in a POST request and returns the PDF.
    Expects the raw .tex content in the request body.
    """
    tex_content = request.get_data(as_text=True)
    if not tex_content:
        return jsonify({"error": "No .tex content provided in the request body."}), 400

    # Use a temporary directory that cleans itself up automatically
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_filename = "document.tex"
        pdf_filename = "document.pdf"
        log_filename = "document.log"

        tex_filepath = os.path.join(temp_dir, tex_filename)
        pdf_filepath = os.path.join(temp_dir, pdf_filename)

        # Write the received TeX content to a file
        with open(tex_filepath, 'w') as f:
            f.write(tex_content)

        # Run the pdflatex command securely
        # -interaction=nonstopmode : Prevents the compiler from pausing for user input on errors.
        # -output-directory       : Ensures all generated files stay in our temp directory.
        command = [
            "pdflatex",
            "-interaction=nonstopmode",
            f"-output-directory={temp_dir}",
            tex_filepath
        ]

        try:
            # Set a timeout to prevent long-running, malicious compilations
            proc = subprocess.run(command, capture_output=True, text=True, timeout=30)

            # If compilation failed, return the error log
            if proc.returncode != 0:
                log_filepath = os.path.join(temp_dir, log_filename)
                with open(log_filepath, 'r') as log_file:
                    log_content = log_file.read()
                return jsonify({
                    "error": "PDF compilation failed.",
                    "logs": log_content
                }), 400

            # If successful, send the generated PDF file back
            return send_file(
                pdf_filepath,
                as_attachment=True,
                download_name='output.pdf',
                mimetype='application/pdf'
            )

        except subprocess.TimeoutExpired:
            return jsonify({"error": "Compilation timed out after 30 seconds."}), 408
        except Exception as e:
            return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)