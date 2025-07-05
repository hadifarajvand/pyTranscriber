#!/usr/bin/env python3
"""
pyTranscriber REST API Server
(C) 2025 Raryel C. Souza - Modified for REST API

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import tempfile
import shutil
import uuid
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename
import multiprocessing

# Add the current directory to Python path to import pytranscriber modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pytranscriber.control.ctr_autosub import Ctr_Autosub
from pytranscriber.control.ctr_whisper import CtrWhisper
from pytranscriber.model.transcription_parameters import Transcription_Parameters
from pytranscriber.util.srtparser import SRTParser
from pytranscriber.util.util import MyUtil

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {
    'audio': {'mp3', 'wav', 'm4a', 'flac', 'ogg', 'aac'},
    'video': {'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'ogv'}
}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Global variables for tracking transcription jobs
transcription_jobs = {}
job_counter = 0

class TranscriptionJob:
    """Represents a transcription job with status tracking."""
    
    def __init__(self, job_id: str, filename: str, engine: str, language: str):
        self.job_id = job_id
        self.filename = filename
        self.engine = engine  # 'autosub' or 'whisper'
        self.language = language
        self.status = 'pending'  # pending, processing, completed, failed
        self.progress = 0
        self.start_time = datetime.now()
        self.end_time = None
        self.error_message = None
        self.output_files = {}
        
    def to_dict(self) -> Dict:
        """Convert job to dictionary for JSON serialization."""
        return {
            'job_id': self.job_id,
            'filename': self.filename,
            'engine': self.engine,
            'language': self.language,
            'status': self.status,
            'progress': self.progress,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error_message': self.error_message,
            'output_files': self.output_files
        }

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ext in ALLOWED_EXTENSIONS['audio'] or ext in ALLOWED_EXTENSIONS['video']

def get_next_job_id() -> str:
    """Generate unique job ID."""
    global job_counter
    job_counter += 1
    return f"job_{job_counter}_{uuid.uuid4().hex[:8]}"

def progress_callback(job_id: str):
    """Progress callback function for transcription engines."""
    def callback(task: str, progress: int):
        if job_id in transcription_jobs:
            transcription_jobs[job_id].progress = progress
            print(f"Job {job_id}: {task} - {progress}%")
    return callback

def transcribe_with_autosub(file_path: str, language: str, job_id: str) -> Tuple[bool, str, Dict]:
    """Transcribe using Google Speech API (autosub)."""
    try:
        # Create output file paths
        base_name = Path(file_path).stem
        output_srt = os.path.join(OUTPUT_FOLDER, f"{base_name}.srt")
        output_txt = os.path.join(OUTPUT_FOLDER, f"{base_name}.txt")
        
        # Initialize autosub
        Ctr_Autosub.init()
        
        # Generate subtitles
        result = Ctr_Autosub.generate_subtitles(
            source_path=file_path,
            output=output_srt,
            src_language=language,
            listener_progress=progress_callback(job_id)
        )
        
        if result == -1:
            return False, "Transcription was cancelled", {}
        
        if not result:
            return False, "Failed to generate subtitles", {}
        
        # Extract text from SRT file
        SRTParser.extractTextFromSRT(output_srt)
        
        # Check if files were created
        if not os.path.exists(output_srt):
            return False, "SRT file was not created", {}
        
        if not os.path.exists(output_txt):
            return False, "TXT file was not created", {}
        
        return True, "Transcription completed successfully", {
            'srt_file': output_srt,
            'txt_file': output_txt
        }
        
    except Exception as e:
        error_msg = f"Autosub transcription failed: {str(e)}\n{traceback.format_exc()}"
        return False, error_msg, {}

def transcribe_with_whisper(file_path: str, language: str, job_id: str, model: str = 'base') -> Tuple[bool, str, Dict]:
    """Transcribe using OpenAI Whisper."""
    try:
        # Initialize Whisper
        CtrWhisper.initialize()
        
        # Create output file paths
        base_name = Path(file_path).stem
        output_srt = os.path.join(OUTPUT_FOLDER, f"{base_name}.srt")
        output_txt = os.path.join(OUTPUT_FOLDER, f"{base_name}.txt")
        
        # Generate subtitles
        result = CtrWhisper.generate_subtitles(
            source_path=file_path,
            src_language=language,
            outputSRT=output_srt,
            outputTXT=output_txt,
            model=model
        )
        
        if result == -1:
            return False, "Transcription was cancelled", {}
        
        if not result:
            return False, "Failed to generate subtitles", {}
        
        # Check if files were created
        if not os.path.exists(output_srt):
            return False, "SRT file was not created", {}
        
        if not os.path.exists(output_txt):
            return False, "TXT file was not created", {}
        
        return True, "Transcription completed successfully", {
            'srt_file': output_srt,
            'txt_file': output_txt
        }
        
    except Exception as e:
        error_msg = f"Whisper transcription failed: {str(e)}\n{traceback.format_exc()}"
        return False, error_msg, {}

def process_transcription_job(job_id: str):
    """Process a transcription job in a separate thread."""
    if job_id not in transcription_jobs:
        return
    
    job = transcription_jobs[job_id]
    job.status = 'processing'
    
    try:
        # Determine transcription engine
        if job.engine == 'autosub':
            success, message, output_files = transcribe_with_autosub(
                job.filename, job.language, job_id
            )
        elif job.engine == 'whisper':
            success, message, output_files = transcribe_with_whisper(
                job.filename, job.language, job_id
            )
        else:
            success = False
            message = f"Unknown transcription engine: {job.engine}"
            output_files = {}
        
        # Update job status
        job.end_time = datetime.now()
        if success:
            job.status = 'completed'
            job.output_files = output_files
            job.progress = 100
        else:
            job.status = 'failed'
            job.error_message = message
            
    except Exception as e:
        job.status = 'failed'
        job.error_message = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
        job.end_time = datetime.now()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/transcribe', methods=['POST'])
def transcribe_file():
    """Upload and transcribe a media file."""
    global transcription_jobs
    
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file
    if not allowed_file(file.filename):
        return jsonify({
            'error': 'File type not allowed. Supported formats: ' + 
                     ', '.join(ALLOWED_EXTENSIONS['audio'] | ALLOWED_EXTENSIONS['video'])
        }), 400
    
    # Get parameters
    engine = request.form.get('engine', 'whisper').lower()  # Default to whisper
    language = request.form.get('language', 'en')  # Default to English
    model = request.form.get('model', 'base')  # For whisper model
    
    # Validate engine
    if engine not in ['autosub', 'whisper']:
        return jsonify({'error': 'Invalid engine. Use "autosub" or "whisper"'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(file_path)
    
    # Create job
    job_id = get_next_job_id()
    job = TranscriptionJob(job_id, file_path, engine, language)
    transcription_jobs[job_id] = job
    
    # Start transcription in background
    import threading
    thread = threading.Thread(target=process_transcription_job, args=(job_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'pending',
        'message': f'Transcription job created. Use /status/{job_id} to check progress.'
    }), 202

@app.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get the status of a transcription job."""
    if job_id not in transcription_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(transcription_jobs[job_id].to_dict())

@app.route('/download/<job_id>/<file_type>', methods=['GET'])
def download_file(job_id, file_type):
    """Download transcription files."""
    if job_id not in transcription_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = transcription_jobs[job_id]
    
    if job.status != 'completed':
        return jsonify({'error': 'Job not completed yet'}), 400
    
    if file_type not in ['srt', 'txt']:
        return jsonify({'error': 'Invalid file type. Use "srt" or "txt"'}), 400
    
    file_key = f'{file_type}_file'
    if file_key not in job.output_files:
        return jsonify({'error': f'{file_type.upper()} file not found'}), 404
    
    file_path = job.output_files[file_key]
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found on disk'}), 404
    
    return send_file(file_path, as_attachment=True)

@app.route('/jobs', methods=['GET'])
def list_jobs():
    """List all transcription jobs."""
    jobs = [job.to_dict() for job in transcription_jobs.values()]
    return jsonify({
        'jobs': jobs,
        'total': len(jobs)
    })

@app.route('/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a transcription job and its files."""
    if job_id not in transcription_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = transcription_jobs[job_id]
    
    # Delete output files
    for file_path in job.output_files.values():
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
    
    # Delete input file
    try:
        if os.path.exists(job.filename):
            os.remove(job.filename)
    except Exception as e:
        print(f"Error deleting input file {job.filename}: {e}")
    
    # Remove job from tracking
    del transcription_jobs[job_id]
    
    return jsonify({'message': 'Job deleted successfully'})

@app.route('/cleanup', methods=['POST'])
def cleanup_old_files():
    """Clean up old files and completed jobs."""
    try:
        # Clean up old files in upload and output folders
        current_time = datetime.now()
        max_age_hours = 24  # Keep files for 24 hours
        
        cleaned_files = 0
        
        for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if (current_time - file_time).total_seconds() > max_age_hours * 3600:
                        os.remove(file_path)
                        cleaned_files += 1
                except Exception as e:
                    print(f"Error cleaning up {file_path}: {e}")
        
        # Clean up old completed/failed jobs
        jobs_to_remove = []
        for job_id, job in transcription_jobs.items():
            if job.end_time and (current_time - job.end_time).total_seconds() > max_age_hours * 3600:
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del transcription_jobs[job_id]
        
        return jsonify({
            'message': f'Cleanup completed. Removed {cleaned_files} files and {len(jobs_to_remove)} jobs.'
        })
        
    except Exception as e:
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({'error': 'File too large. Maximum size is 500MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Set multiprocessing start method for macOS
    if sys.platform == 'darwin':
        multiprocessing.set_start_method('spawn')
    
    # Configure Flask
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    
    print("pyTranscriber REST API Server")
    print("=" * 40)
    print("Available endpoints:")
    print("  POST /transcribe     - Upload and transcribe a file")
    print("  GET  /status/<id>    - Check job status")
    print("  GET  /download/<id>/<type> - Download SRT or TXT file")
    print("  GET  /jobs           - List all jobs")
    print("  DELETE /jobs/<id>    - Delete a job")
    print("  POST /cleanup        - Clean up old files")
    print("  GET  /health         - Health check")
    print("=" * 40)
    
    # Run the server
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True) 