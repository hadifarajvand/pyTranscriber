# pyTranscriber REST API Server

A REST API server that provides transcription services using the pyTranscriber engine. This API allows you to upload audio/video files and receive transcription results in SRT and TXT formats.

## Features

- **Dual Engine Support**: Both Google Speech API (autosub) and OpenAI Whisper
- **Async Processing**: Non-blocking transcription with job status tracking
- **Multiple Formats**: Support for various audio and video formats
- **Progress Tracking**: Real-time progress updates for transcription jobs
- **File Management**: Automatic cleanup of old files and jobs
- **CORS Support**: Cross-origin resource sharing enabled
- **Error Handling**: Comprehensive error handling and logging

## Supported File Formats

### Audio Formats
- MP3, WAV, M4A, FLAC, OGG, AAC

### Video Formats
- MP4, AVI, MKV, MOV, WMV, FLV, WebM, OGV

## Installation

### Prerequisites

1. **Python 3.8+**
2. **FFmpeg** - Required for audio/video processing

#### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

### Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd pyTranscriber
```

2. **Install dependencies:**
```bash
pip install -r api_requirements.txt
```

3. **Run the server:**
```bash
python api_server.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### 1. Health Check
**GET** `/health`

Check if the server is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:30:00",
  "version": "1.0.0"
}
```

### 2. Transcribe File
**POST** `/transcribe`

Upload and transcribe a media file.

**Parameters:**
- `file` (required): The audio/video file to transcribe
- `engine` (optional): Transcription engine - `"autosub"` or `"whisper"` (default: `"whisper"`)
- `language` (optional): Language code (default: `"en"`)
- `model` (optional): Whisper model size - `"tiny"`, `"base"`, `"small"`, `"medium"`, `"large"` (default: `"base"`)

**Example using curl:**
```bash
curl -X POST http://localhost:5000/transcribe \
  -F "file=@audio.mp3" \
  -F "engine=whisper" \
  -F "language=en" \
  -F "model=base"
```

**Response:**
```json
{
  "job_id": "job_1_a1b2c3d4",
  "status": "pending",
  "message": "Transcription job created. Use /status/job_1_a1b2c3d4 to check progress."
}
```

### 3. Check Job Status
**GET** `/status/{job_id}`

Get the current status of a transcription job.

**Response:**
```json
{
  "job_id": "job_1_a1b2c3d4",
  "filename": "/path/to/uploaded/file.mp3",
  "engine": "whisper",
  "language": "en",
  "status": "completed",
  "progress": 100,
  "start_time": "2025-01-27T10:30:00",
  "end_time": "2025-01-27T10:32:15",
  "error_message": null,
  "output_files": {
    "srt_file": "/path/to/output/file.srt",
    "txt_file": "/path/to/output/file.txt"
  }
}
```

### 4. Download Transcription Files
**GET** `/download/{job_id}/{file_type}`

Download the transcription files (SRT or TXT).

**Parameters:**
- `job_id`: The transcription job ID
- `file_type`: `"srt"` or `"txt"`

**Example:**
```bash
curl -O http://localhost:5000/download/job_1_a1b2c3d4/srt
curl -O http://localhost:5000/download/job_1_a1b2c3d4/txt
```

### 5. List All Jobs
**GET** `/jobs`

Get a list of all transcription jobs.

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "job_1_a1b2c3d4",
      "filename": "/path/to/file.mp3",
      "engine": "whisper",
      "language": "en",
      "status": "completed",
      "progress": 100,
      "start_time": "2025-01-27T10:30:00",
      "end_time": "2025-01-27T10:32:15",
      "error_message": null,
      "output_files": {
        "srt_file": "/path/to/output/file.srt",
        "txt_file": "/path/to/output/file.txt"
      }
    }
  ],
  "total": 1
}
```

### 6. Delete Job
**DELETE** `/jobs/{job_id}`

Delete a transcription job and its associated files.

**Response:**
```json
{
  "message": "Job deleted successfully"
}
```

### 7. Cleanup Old Files
**POST** `/cleanup`

Clean up old files and completed jobs (older than 24 hours).

**Response:**
```json
{
  "message": "Cleanup completed. Removed 5 files and 3 jobs."
}
```

## Job Status Values

- `pending`: Job is queued for processing
- `processing`: Job is currently being processed
- `completed`: Job completed successfully
- `failed`: Job failed with an error

## Language Codes

### Google Speech API (autosub)
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ru` - Russian
- `ja` - Japanese
- `ko` - Korean
- `zh` - Chinese (Simplified)
- `zh-TW` - Chinese (Traditional)

### OpenAI Whisper
Whisper supports 99+ languages. Common codes:
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ru` - Russian
- `ja` - Japanese
- `ko` - Korean
- `zh` - Chinese

## Whisper Models

- `tiny`: Fastest, least accurate
- `base`: Good balance of speed and accuracy
- `small`: Better accuracy, slower
- `medium`: High accuracy, slower
- `large`: Best accuracy, slowest

## Usage Examples

### Python Client Example

```python
import requests
import time

# Upload and transcribe
with open('audio.mp3', 'rb') as f:
    response = requests.post('http://localhost:5000/transcribe', 
                           files={'file': f},
                           data={'engine': 'whisper', 'language': 'en'})
    
job_id = response.json()['job_id']

# Check status
while True:
    status_response = requests.get(f'http://localhost:5000/status/{job_id}')
    status = status_response.json()
    
    if status['status'] == 'completed':
        # Download files
        srt_response = requests.get(f'http://localhost:5000/download/{job_id}/srt')
        txt_response = requests.get(f'http://localhost:5000/download/{job_id}/txt')
        
        with open('transcript.srt', 'wb') as f:
            f.write(srt_response.content)
        with open('transcript.txt', 'wb') as f:
            f.write(txt_response.content)
        break
    elif status['status'] == 'failed':
        print(f"Transcription failed: {status['error_message']}")
        break
    
    time.sleep(5)  # Wait 5 seconds before checking again
```

### JavaScript Client Example

```javascript
async function transcribeFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('engine', 'whisper');
    formData.append('language', 'en');
    
    // Start transcription
    const response = await fetch('http://localhost:5000/transcribe', {
        method: 'POST',
        body: formData
    });
    
    const { job_id } = await response.json();
    
    // Poll for completion
    while (true) {
        const statusResponse = await fetch(`http://localhost:5000/status/${job_id}`);
        const status = await statusResponse.json();
        
        if (status.status === 'completed') {
            // Download files
            const srtResponse = await fetch(`http://localhost:5000/download/${job_id}/srt`);
            const txtResponse = await fetch(`http://localhost:5000/download/${job_id}/txt`);
            
            const srtBlob = await srtResponse.blob();
            const txtBlob = await txtResponse.blob();
            
            // Save files
            const srtUrl = URL.createObjectURL(srtBlob);
            const txtUrl = URL.createObjectURL(txtBlob);
            
            const srtLink = document.createElement('a');
            srtLink.href = srtUrl;
            srtLink.download = 'transcript.srt';
            srtLink.click();
            
            const txtLink = document.createElement('a');
            txtLink.href = txtUrl;
            txtLink.download = 'transcript.txt';
            txtLink.click();
            
            break;
        } else if (status.status === 'failed') {
            console.error('Transcription failed:', status.error_message);
            break;
        }
        
        await new Promise(resolve => setTimeout(resolve, 5000));
    }
}
```

## Configuration

### Environment Variables

You can configure the server using environment variables:

- `UPLOAD_FOLDER`: Directory for uploaded files (default: `uploads`)
- `OUTPUT_FOLDER`: Directory for output files (default: `outputs`)
- `MAX_CONTENT_LENGTH`: Maximum file size in bytes (default: 500MB)
- `FLASK_ENV`: Flask environment (default: `production`)

### Google Speech API Key

For autosub engine, you need to set the Google Speech API key:

```bash
export GOOGLE_SPEECH_API_KEY="your-api-key-here"
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `202`: Job accepted (for transcription requests)
- `400`: Bad request (invalid parameters)
- `404`: Not found (job doesn't exist)
- `413`: File too large
- `500`: Internal server error

## Security Considerations

- The API server is designed for development and internal use
- For production deployment, consider:
  - Adding authentication/authorization
  - Using HTTPS
  - Implementing rate limiting
  - Setting up proper logging
  - Using a production WSGI server (Gunicorn, uWSGI)

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Install FFmpeg and ensure it's in your PATH
2. **Google Speech API errors**: Check your API key and quota
3. **Whisper model download issues**: Ensure internet connection for first-time model downloads
4. **Memory issues**: Use smaller Whisper models for large files

### Logs

The server prints progress and error messages to stdout. Monitor these for debugging:

```bash
python api_server.py 2>&1 | tee server.log
```

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details. 