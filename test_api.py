#!/usr/bin/env python3
"""
Test script for pyTranscriber REST API Server
Demonstrates how to use the API endpoints
"""

import requests
import time
import os
import sys
from pathlib import Path

# API base URL
API_BASE = "http://localhost:5000"

def test_health():
    """Test the health endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Server is healthy: {data}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Make sure it's running on localhost:5000")
        return False

def test_transcribe_whisper(file_path):
    """Test transcription using Whisper engine."""
    print(f"\nTesting Whisper transcription with file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"✗ File not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{API_BASE}/transcribe",
                files={'file': f},
                data={
                    'engine': 'whisper',
                    'language': 'en',
                    'model': 'base'
                }
            )
        
        if response.status_code == 202:
            data = response.json()
            job_id = data['job_id']
            print(f"✓ Transcription job created: {job_id}")
            return job_id
        else:
            print(f"✗ Transcription request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Error during transcription request: {e}")
        return None

def test_transcribe_autosub(file_path):
    """Test transcription using Google Speech API (autosub)."""
    print(f"\nTesting Autosub transcription with file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"✗ File not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{API_BASE}/transcribe",
                files={'file': f},
                data={
                    'engine': 'autosub',
                    'language': 'en'
                }
            )
        
        if response.status_code == 202:
            data = response.json()
            job_id = data['job_id']
            print(f"✓ Transcription job created: {job_id}")
            return job_id
        else:
            print(f"✗ Transcription request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Error during transcription request: {e}")
        return None

def wait_for_completion(job_id, timeout=300):
    """Wait for a transcription job to complete."""
    print(f"Waiting for job {job_id} to complete...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{API_BASE}/status/{job_id}")
            if response.status_code == 200:
                status = response.json()
                print(f"Status: {status['status']} - Progress: {status['progress']}%")
                
                if status['status'] == 'completed':
                    print("✓ Transcription completed successfully!")
                    return status
                elif status['status'] == 'failed':
                    print(f"✗ Transcription failed: {status['error_message']}")
                    return status
                
                time.sleep(5)  # Wait 5 seconds before checking again
            else:
                print(f"✗ Failed to get status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ Error checking status: {e}")
            return None
    
    print(f"✗ Timeout waiting for job completion (>{timeout}s)")
    return None

def download_files(job_id, output_dir="downloads"):
    """Download transcription files."""
    print(f"\nDownloading files for job {job_id}...")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Download SRT file
        srt_response = requests.get(f"{API_BASE}/download/{job_id}/srt")
        if srt_response.status_code == 200:
            srt_path = os.path.join(output_dir, f"{job_id}.srt")
            with open(srt_path, 'wb') as f:
                f.write(srt_response.content)
            print(f"✓ Downloaded SRT file: {srt_path}")
        else:
            print(f"✗ Failed to download SRT: {srt_response.status_code}")
        
        # Download TXT file
        txt_response = requests.get(f"{API_BASE}/download/{job_id}/txt")
        if txt_response.status_code == 200:
            txt_path = os.path.join(output_dir, f"{job_id}.txt")
            with open(txt_path, 'wb') as f:
                f.write(txt_response.content)
            print(f"✓ Downloaded TXT file: {txt_path}")
        else:
            print(f"✗ Failed to download TXT: {txt_response.status_code}")
            
    except Exception as e:
        print(f"✗ Error downloading files: {e}")

def test_list_jobs():
    """Test listing all jobs."""
    print("\nTesting list jobs endpoint...")
    try:
        response = requests.get(f"{API_BASE}/jobs")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data['total']} jobs")
            for job in data['jobs']:
                print(f"  - {job['job_id']}: {job['status']} ({job['progress']}%)")
            return True
        else:
            print(f"✗ Failed to list jobs: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error listing jobs: {e}")
        return False

def test_cleanup():
    """Test cleanup endpoint."""
    print("\nTesting cleanup endpoint...")
    try:
        response = requests.post(f"{API_BASE}/cleanup")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Cleanup completed: {data['message']}")
            return True
        else:
            print(f"✗ Cleanup failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error during cleanup: {e}")
        return False

def main():
    """Main test function."""
    print("pyTranscriber REST API Test Script")
    print("=" * 40)
    
    # Test health endpoint
    if not test_health():
        print("\nServer is not available. Please start the API server first:")
        print("python api_server.py")
        return
    
    # Test with a sample audio file if provided
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        print(f"\nUsing test file: {test_file}")
        
        # Test Whisper transcription
        job_id = test_transcribe_whisper(test_file)
        if job_id:
            status = wait_for_completion(job_id)
            if status and status['status'] == 'completed':
                download_files(job_id)
        
        # Test Autosub transcription (if Google API key is available)
        if os.environ.get('GOOGLE_SPEECH_API_KEY'):
            job_id = test_transcribe_autosub(test_file)
            if job_id:
                status = wait_for_completion(job_id)
                if status and status['status'] == 'completed':
                    download_files(job_id)
        else:
            print("\nSkipping Autosub test (GOOGLE_SPEECH_API_KEY not set)")
    
    # Test other endpoints
    test_list_jobs()
    test_cleanup()
    
    print("\nTest completed!")

if __name__ == "__main__":
    main() 