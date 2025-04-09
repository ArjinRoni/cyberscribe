# CyberScribe Transcriptor

A transcription tool created by Claude Sonnet and Arjin, CyberScribe helps to make more efficient human - AI interaction, often constrained by the discrepancy btw human token creation and deployment speed. It helps us meetsacks communicate with text based llm interfaces faster. You can instantly record your brainstorming / thoughts sesh / long prompt, or intended communication with any llm and paste it into any text box. It also accepts audio and video files, for example WhatsApp audio messages, or iphone / phone recordings. 

humans speak at ~150 Word Per Minute but type only ~50 WPM. This blocks reasoning / articulation steps as well. 

 Simply speak, transcribe, and paste into any LLM your output after loading the transcription model. I use base but better computers can use small. 

![CyberScribe Logo](https://img.shields.io/badge/CyberScribe-v1.1-00ff00?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0iIzAwZmYwMCIgZD0iTTIzIDh2OGgtNHYtMmgtMnYyaC00di0ySDl2Mkg1VjhoNHYyaDR2LTJoMnYyaDJ2LTJoNnptLTEwIDZoLTJ2MmgydjJ6Ii8+PC9zdmc+)

## Features

- 🎙️ **Live Recording Transcription** - Record audio directly and get instant transcriptions
- 🎬 **Video File Support** - Extract and transcribe audio from video files
- 📊 **Multiple Model Sizes** - Choose from tiny, base, small, medium, or large Whisper models
- 📋 **Copy to Clipboard** - One-click copying of transcription results
- 📁 **Batch Processing** - Process multiple audio/video files in sequence
- 🔍 **Search History** - Search through past transcriptions
- 📤 **Export Options** - Export as TXT, JSON, or SRT subtitle format
- ⚡ **Segmented Processing** - Process large files in segments for faster partial results

## Requirements

- Python 3.10+ (tested with Python 3.12)
- FFmpeg (external dependency, required for video file processing)
- A microphone (for live recording)
- GPU recommended for larger models (medium and large)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/transcriptor.git
cd transcriptor
```

### 2. Create and Activate Virtual Environment

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install FFmpeg (if not already installed)

#### Windows
1. Download FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract the archive and add the bin folder to your PATH environment variable

#### macOS (using Homebrew)
```bash
brew install ffmpeg
```

#### Linux (Debian/Ubuntu)
```bash
sudo apt update
sudo apt install ffmpeg
```

## Usage

### Starting the Application

#### Windows
```bash
transcriptor.bat
```
or
```bash
venv\Scripts\python transcriptor.py
```

#### macOS/Linux
```bash
./transcriptor.py
```
or
```bash
python3 transcriptor.py
```

### Using the Application

1. **Load Model**: Select a model size and click [LOAD MODEL]
2. **Transcribe Audio**: 
   - Click [START RECORDING] to record and transcribe live audio
   - Click [LOAD AUDIO FILE] to transcribe an existing audio or video file
   - Click [BATCH PROCESS] to transcribe multiple files in sequence
3. **Manage Results**:
   - Copy transcriptions with [COPY LATEST]
   - Export transcriptions in different formats with [EXPORT]
   - View and search history in the HISTORY tab

## Model Size Comparison

| Model | Accuracy | Speed | Memory Usage |
|-------|----------|-------|--------------|
| tiny  | Lowest   | Fastest | ~1GB     |
| base  | Low      | Fast    | ~1GB     |
| small | Medium   | Medium  | ~2GB     |
| medium| High     | Slow    | ~5GB     |
| large | Highest  | Slowest | ~10GB    |

## Troubleshooting

- **Error loading models**: Ensure you have enough free RAM for the selected model size
- **Video files not supported**: Install moviepy with `pip install moviepy`
- **Audio not recording**: Check your microphone settings and permissions
- **FFmpeg errors**: Ensure FFmpeg is correctly installed and in your PATH

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the speech recognition model
- [MoviePy](https://zulko.github.io/moviepy/) for video file handling
- [FFmpeg](https://ffmpeg.org/) for audio processing 
