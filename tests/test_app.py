import pytest
from unittest.mock import patch, MagicMock
import subprocess
import sys
import os

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'pdflatex_present' in data

def test_compile_no_content(client):
    """Test compilation with empty body."""
    response = client.post('/compile', data='')
    assert response.status_code == 400
    assert b"No .tex content" in response.data

@patch('subprocess.run')
def test_compile_success(mock_run, client):
    """Test successful compilation."""
    # Mock successful subprocess execution
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_run.return_value = mock_proc

    # We need to mock os.path.exists to return True for the pdf file
    # and open to return some dummy content.
    # However, app.py uses send_file which interacts with the filesystem.
    # It's easier to let it write to the temp dir, but we mocked subprocess so no PDF is created.
    # We can mock send_file or just ensure the subprocess was called correctly.
    
    # To make this test run without creating files, we can mock send_file
    with patch('app.send_file') as mock_send_file:
        mock_send_file.return_value = "PDF CONTENT"
        
        tex_content = "\\documentclass{article}\\begin{document}Test\\end{document}"
        response = client.post('/compile', data=tex_content)
        
        assert response.status_code == 200
        # Verify subprocess was called
        assert mock_run.called
        args, kwargs = mock_run.call_args
        assert args[0][0] == 'pdflatex'
        assert kwargs['timeout'] == 30 # Default timeout

@patch('subprocess.run')
def test_compile_failure(mock_run, client):
    """Test compilation failure (e.g. syntax error)."""
    # Mock failed subprocess execution
    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stdout = "Error log"
    mock_proc.stderr = ""
    mock_run.return_value = mock_proc

    tex_content = "\\invalidcommand"
    response = client.post('/compile', data=tex_content)
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == "PDF compilation failed."

@patch('subprocess.run')
def test_compile_timeout(mock_run, client):
    """Test compilation timeout."""
    # Mock timeout
    mock_run.side_effect = subprocess.TimeoutExpired(cmd='pdflatex', timeout=30)

    tex_content = "\\documentclass{article}..."
    response = client.post('/compile', data=tex_content)
    
    assert response.status_code == 408
    assert b"timed out" in response.data
