import os
import subprocess
import tempfile
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

# --- NEW: SECURITY SCANNER ---
# Define a list of TeX commands that are too dangerous to allow.
# \write18 is shell escape. The others can access the filesystem.
DANGEROUS_COMMANDS = [
    "\\write18",
    "\\input",
    "\\openin",
    "\\openout",
    "\\def",          # Can be used to redefine safe commands maliciously
    "\\unexpanded",   # Can be used to bypass simple string checks
    "\\obeyspaces",   # Can obscure malicious code
]
# -----------------------------


@app.route('/compile', methods=['POST'])
def compile_tex():
    tex_content = request.get_data(as_text=True)
    if not tex_content:
        return jsonify({"error": "No .tex content provided in the request body."}), 400

    # --- NEW: Run the security check ---
    for command in DANGEROUS_COMMANDS:
        if command in tex_content:
            return jsonify({
                "error": "Security check failed.",
                "message": f"Disallowed command '{command}' found in input."
            }), 403 # 403 Forbidden is a fitting status code

    # -----------------------------------

    with tempfile.TemporaryDirectory() as temp_dir:
        tex_filename = "document.tex"
        pdf_filename = "document.pdf"
        log_filename = "document.log"

        tex_filepath = os.path.join(temp_dir, tex_filename)
        pdf_filepath = os.path.join(temp_dir, pdf_filename)

        with open(tex_filepath, 'w') as f:
            f.write(tex_content)

        command = [
            "pdflatex",
            "-interaction=nonstopmode",
            f"-output-directory={temp_dir}",
            tex_filepath
        ]

        try:
            proc = subprocess.run(command, capture_output=True, text=True, timeout=30)

            if proc.returncode != 0:
                log_filepath = os.path.join(temp_dir, log_filename)
                log_content = ""
                # It's possible for the log file to not be created on a fatal error
                if os.path.exists(log_filepath):
                    with open(log_filepath, 'r') as log_file:
                        log_content = log_file.read()
                return jsonify({
                    "error": "PDF compilation failed.",
                    "logs": log_content
                }), 400

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