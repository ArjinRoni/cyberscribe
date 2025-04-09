import whisper
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pyaudio
import wave
from datetime import datetime, timedelta
import time
import pyperclip
import uuid
import json
import re
import tempfile
import math

# Try to import moviepy for video file handling
try:
    from moviepy.editor import VideoFileClip, AudioFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

ASCII_ART = """
╔══════════════════════════════════════════╗
║  ╔╦╗╦═╗╔═╗╔╗╔╔═╗╔═╗╦═╗╦╔╗ ╔═╗╦═╗       ║
║   ║ ╠╦╝╠═╣║║║╚═╗║  ╠╦╝║╠╩╗║╣ ╠╦╝       ║
║   ╩ ╩╚═╩ ╩╝╚╝╚═╝╚═╝╩╚═╩╚═╝╚═╝╩╚═ v1.1  ║
╚══════════════════════════════════════════╝
"""

# Constants
HISTORY_FILE = "deliberations.txt"
HISTORY_JSON = "transcription_history.json"

class TranscriptorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CyberScribe v1.1")
        self.root.geometry("800x600")
        self.root.configure(bg='black')
        
        # Initialize transcriptor
        self.transcriptor = None
        self.recording = False
        self.audio = pyaudio.PyAudio()
        self.latest_transcription = ""
        
        # Session tracking
        self.session_id = self.generate_session_id()
        self.session_start_time = datetime.now()
        self.session_transcriptions = []
        
        # Configure style
        self.configure_style()
        self.create_widgets()
        
        # Create history directory if it doesn't exist
        os.makedirs("history", exist_ok=True)
        
    def generate_session_id(self):
        """Generate a unique session ID"""
        return f"SESSION_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
    def configure_style(self):
        style = ttk.Style()
        style.configure("Cyberpunk.TFrame", background="black")
        style.configure("Cyberpunk.TButton", 
                       background="#00ff00",
                       foreground="black",
                       font=("Courier", 10, "bold"),
                       padding=5)
        style.configure("Cyberpunk.TLabel", 
                       background="black",
                       foreground="#00ff00",
                       font=("Courier", 10))
        style.configure("Copy.TButton",
                       background="#444444",
                       foreground="#00ff00",
                       font=("Courier", 10, "bold"),
                       padding=5)
        style.configure("Tab.TNotebook", background="black")
        style.map("Tab.TNotebook.Tab",
                 background=[("selected", "#00ff00"), ("!selected", "black")],
                 foreground=[("selected", "black"), ("!selected", "#00ff00")])
        
    def create_widgets(self):
        # ASCII Art
        ascii_label = tk.Label(self.root, 
                             text=ASCII_ART,
                             fg="#00ff00",
                             bg="black",
                             font=("Courier", 10))
        ascii_label.pack(pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root, style="Tab.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Main tab
        self.main_tab = ttk.Frame(self.notebook, style="Cyberpunk.TFrame")
        self.notebook.add(self.main_tab, text="TRANSCRIBE")
        
        # History tab
        self.history_tab = ttk.Frame(self.notebook, style="Cyberpunk.TFrame")
        self.notebook.add(self.history_tab, text="HISTORY")
        
        # Create main tab widgets
        self.create_main_tab_widgets()
        
        # Create history tab widgets
        self.create_history_tab_widgets()
        
        # Session info label
        self.session_label = ttk.Label(self.root, 
                                     text=f"SESSION ID: {self.session_id}",
                                     style="Cyberpunk.TLabel")
        self.session_label.pack(side="bottom", pady=5)
        
    def create_main_tab_widgets(self):
        # Model selection
        model_frame = ttk.Frame(self.main_tab, style="Cyberpunk.TFrame")
        model_frame.pack(fill="x", pady=5, padx=20)
        
        ttk.Label(model_frame, 
                 text="[SELECT MODEL]:",
                 style="Cyberpunk.TLabel").pack(side="left")
        
        self.model_var = tk.StringVar(value="base")
        model_combo = ttk.Combobox(model_frame, 
                                 textvariable=self.model_var,
                                 values=["tiny", "base", "small", "medium", "large"],
                                 state="readonly",
                                 width=10)
        model_combo.pack(side="left", padx=5)
        
        self.load_button = ttk.Button(model_frame, 
                                    text="[LOAD MODEL]",
                                    command=self.load_model,
                                    style="Cyberpunk.TButton")
        self.load_button.pack(side="left", padx=5)
        
        # File transcription button
        self.file_button = ttk.Button(model_frame,
                                    text="[LOAD AUDIO FILE]",
                                    command=self.load_audio_file,
                                    style="Cyberpunk.TButton")
        self.file_button.pack(side="left", padx=5)
        
        # Batch processing button
        self.batch_button = ttk.Button(model_frame,
                                     text="[BATCH PROCESS]",
                                     command=self.batch_process_files,
                                     style="Cyberpunk.TButton")
        self.batch_button.pack(side="left", padx=5)
        
        # Recording controls
        record_frame = ttk.Frame(self.main_tab, style="Cyberpunk.TFrame")
        record_frame.pack(fill="x", pady=5, padx=20)
        
        self.record_button = ttk.Button(record_frame,
                                      text="[START RECORDING]",
                                      command=self.toggle_recording,
                                      style="Cyberpunk.TButton")
        self.record_button.pack(side="left", padx=5)
        
        self.status_label = ttk.Label(record_frame,
                                    text="STATUS: IDLE",
                                    style="Cyberpunk.TLabel")
        self.status_label.pack(side="left", padx=5)
        
        # Control Frame
        control_frame = ttk.Frame(self.main_tab, style="Cyberpunk.TFrame")
        control_frame.pack(fill="x", pady=5, padx=20)
        
        # Copy button
        self.copy_button = ttk.Button(control_frame,
                                    text="[COPY LATEST]",
                                    command=self.copy_latest,
                                    style="Copy.TButton",
                                    state="disabled")
        self.copy_button.pack(side="right", padx=5)
        
        # Export button
        self.export_button = ttk.Button(control_frame,
                                      text="[EXPORT]",
                                      command=self.export_transcription,
                                      style="Cyberpunk.TButton",
                                      state="disabled")
        self.export_button.pack(side="right", padx=5)
        
        # Word count label
        self.word_count_label = ttk.Label(control_frame,
                                        text="WORDS: 0",
                                        style="Cyberpunk.TLabel")
        self.word_count_label.pack(side="right", padx=10)
        
        # Output display with scrollbar
        output_frame = ttk.Frame(self.main_tab, style="Cyberpunk.TFrame")
        output_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(output_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.output_text = tk.Text(output_frame,
                                 wrap="word",
                                 height=20,
                                 bg="black",
                                 fg="#00ff00",
                                 font=("Courier", 10),
                                 yscrollcommand=scrollbar.set)
        self.output_text.pack(fill="both", expand=True)
        scrollbar.config(command=self.output_text.yview)
        
        # Add some cyberpunk flair
        self.output_text.insert("1.0", "SYSTEM READY...\n" + "="*50 + "\n")
        
    def create_history_tab_widgets(self):
        # Search frame
        search_frame = ttk.Frame(self.history_tab, style="Cyberpunk.TFrame")
        search_frame.pack(fill="x", pady=5, padx=20)
        
        ttk.Label(search_frame, 
                 text="[SEARCH]:",
                 style="Cyberpunk.TLabel").pack(side="left")
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, 
                               textvariable=self.search_var,
                               width=30)
        search_entry.pack(side="left", padx=5)
        
        search_button = ttk.Button(search_frame,
                                 text="[FIND]",
                                 command=self.search_history,
                                 style="Cyberpunk.TButton")
        search_button.pack(side="left", padx=5)
        
        # History controls
        history_control_frame = ttk.Frame(self.history_tab, style="Cyberpunk.TFrame")
        history_control_frame.pack(fill="x", pady=5, padx=20)
        
        refresh_button = ttk.Button(history_control_frame,
                                  text="[REFRESH]",
                                  command=self.load_history,
                                  style="Cyberpunk.TButton")
        refresh_button.pack(side="left", padx=5)
        
        export_button = ttk.Button(history_control_frame,
                                 text="[EXPORT]",
                                 command=self.export_history,
                                 style="Cyberpunk.TButton")
        export_button.pack(side="left", padx=5)
        
        # History display with scrollbar
        history_frame = ttk.Frame(self.history_tab, style="Cyberpunk.TFrame")
        history_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Add scrollbar
        history_scrollbar = ttk.Scrollbar(history_frame)
        history_scrollbar.pack(side="right", fill="y")
        
        self.history_text = scrolledtext.ScrolledText(history_frame,
                                                   wrap="word",
                                                   height=20,
                                                   bg="black",
                                                   fg="#00ff00",
                                                   font=("Courier", 10))
        self.history_text.pack(fill="both", expand=True)
        
        # Load history on startup
        self.load_history()
        
    def toggle_recording(self):
        if not self.transcriptor:
            messagebox.showerror("Error", "Please load the model first!")
            return
            
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        self.recording = True
        self.record_button.configure(text="[STOP RECORDING]")
        self.status_label.configure(text="STATUS: RECORDING")
        
        # Start recording in chunks
        self.frames = []
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                    channels=1,
                                    rate=44100,
                                    input=True,
                                    frames_per_buffer=1024,
                                    stream_callback=self.audio_callback)
        self.stream.start_stream()
        
    def audio_callback(self, in_data, frame_count, time_info, status):
        self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)
        
    def stop_recording(self):
        self.recording = False
        self.stream.stop_stream()
        self.stream.close()
        
        # Save the recording
        temp_file = "temp_recording.wav"
        wf = wave.open(temp_file, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        
        # Transcribe the recording
        self.status_label.configure(text="STATUS: TRANSCRIBING")
        result = self.transcriptor.transcribe_file(temp_file)
        
        # Log the transcription
        self.log_transcription(result)
        
        # Store the latest transcription
        self.latest_transcription = result
        
        # Update word count
        word_count = len(result.split())
        self.word_count_label.configure(text=f"WORDS: {word_count}")
        
        # Enable copy and export buttons
        self.copy_button.configure(state="normal")
        self.export_button.configure(state="normal")
        
        # Display the result with cyberpunk formatting
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.output_text.insert("1.0", f"\n{'='*50}\n")
        self.output_text.insert("1.0", f"{result}\n")
        self.output_text.insert("1.0", f"[TIMESTAMP: {timestamp}]\n")
        self.output_text.insert("1.0", f"[RECORDING_{timestamp.replace(':', '')}]\n")
        
        self.record_button.configure(text="[START RECORDING]")
        self.status_label.configure(text="STATUS: IDLE")
        
        # Clean up
        os.remove(temp_file)
        
    def log_transcription(self, text):
        """Enhanced logging with session tracking and JSON format"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Log to text file (for backward compatibility)
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"SESSION: {self.session_id}\n")
            f.write(f"TIMESTAMP: {timestamp}\n")
            f.write(f"{text}\n")
            f.write(f"{'='*50}\n")
        
        # Create transcription entry
        transcription_entry = {
            "session_id": self.session_id,
            "timestamp": timestamp,
            "text": text,
            "word_count": len(text.split())
        }
        
        # Add to session transcriptions
        self.session_transcriptions.append(transcription_entry)
        
        # Save to JSON history file
        self.save_json_history(transcription_entry)
        
        # Update history tab if it's visible
        if self.notebook.index("current") == 1:  # History tab is selected
            self.load_history()
    
    def save_json_history(self, entry):
        """Save transcription to JSON history file"""
        # Load existing history if available
        history = []
        if os.path.exists(HISTORY_JSON):
            try:
                with open(HISTORY_JSON, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                # If file is corrupted, start fresh
                history = []
        
        # Add new entry
        history.append(entry)
        
        # Save updated history
        with open(HISTORY_JSON, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    
    def load_history(self):
        """Load and display transcription history"""
        self.history_text.config(state="normal")
        self.history_text.delete(1.0, tk.END)
        
        # First try to load from JSON file
        if os.path.exists(HISTORY_JSON):
            try:
                with open(HISTORY_JSON, "r", encoding="utf-8") as f:
                    history = json.load(f)
                
                # Display history in reverse chronological order
                for entry in reversed(history):
                    session_id = entry.get("session_id", "UNKNOWN_SESSION")
                    timestamp = entry.get("timestamp", "UNKNOWN_TIME")
                    text = entry.get("text", "")
                    word_count = entry.get("word_count", 0)
                    
                    self.history_text.insert(tk.END, f"[SESSION: {session_id}]\n")
                    self.history_text.insert(tk.END, f"[TIMESTAMP: {timestamp}]\n")
                    self.history_text.insert(tk.END, f"[WORDS: {word_count}]\n")
                    self.history_text.insert(tk.END, f"{text}\n")
                    self.history_text.insert(tk.END, f"{'='*50}\n\n")
                
                self.history_text.insert(tk.END, f"TOTAL ENTRIES: {len(history)}\n")
                
            except Exception as e:
                # Fallback to text file if JSON fails
                self.load_text_history()
        else:
            # Fallback to text file if JSON doesn't exist
            self.load_text_history()
        
        self.history_text.config(state="disabled")
    
    def load_text_history(self):
        """Fallback method to load history from text file"""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                self.history_text.insert(tk.END, content)
        else:
            self.history_text.insert(tk.END, "No history found.\n")
    
    def search_history(self):
        """Search through transcription history"""
        query = self.search_var.get().strip().lower()
        if not query:
            messagebox.showinfo("Search", "Please enter a search term")
            return
        
        self.history_text.config(state="normal")
        self.history_text.delete(1.0, tk.END)
        
        # Search in JSON history
        if os.path.exists(HISTORY_JSON):
            try:
                with open(HISTORY_JSON, "r", encoding="utf-8") as f:
                    history = json.load(f)
                
                # Filter entries containing the search query
                matches = [entry for entry in history if query in entry.get("text", "").lower()]
                
                if matches:
                    for entry in reversed(matches):
                        session_id = entry.get("session_id", "UNKNOWN_SESSION")
                        timestamp = entry.get("timestamp", "UNKNOWN_TIME")
                        text = entry.get("text", "")
                        word_count = entry.get("word_count", 0)
                        
                        self.history_text.insert(tk.END, f"[SESSION: {session_id}]\n")
                        self.history_text.insert(tk.END, f"[TIMESTAMP: {timestamp}]\n")
                        self.history_text.insert(tk.END, f"[WORDS: {word_count}]\n")
                        self.history_text.insert(tk.END, f"{text}\n")
                        self.history_text.insert(tk.END, f"{'='*50}\n\n")
                    
                    self.history_text.insert(tk.END, f"FOUND {len(matches)} MATCHES\n")
                else:
                    self.history_text.insert(tk.END, f"No matches found for '{query}'\n")
            except Exception as e:
                self.history_text.insert(tk.END, f"Error searching history: {str(e)}\n")
        else:
            self.history_text.insert(tk.END, "No history database found.\n")
        
        self.history_text.config(state="disabled")
    
    def export_history(self):
        """Export history to a file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export History"
        )
        
        if not file_path:
            return
        
        try:
            # If JSON history exists, use that for export
            if os.path.exists(HISTORY_JSON):
                with open(HISTORY_JSON, "r", encoding="utf-8") as f:
                    history = json.load(f)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"CYBERSCRIBE TRANSCRIPTION HISTORY\n")
                    f.write(f"EXPORTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"{'='*50}\n\n")
                    
                    for entry in reversed(history):
                        session_id = entry.get("session_id", "UNKNOWN_SESSION")
                        timestamp = entry.get("timestamp", "UNKNOWN_TIME")
                        text = entry.get("text", "")
                        word_count = entry.get("word_count", 0)
                        
                        f.write(f"SESSION: {session_id}\n")
                        f.write(f"TIMESTAMP: {timestamp}\n")
                        f.write(f"WORDS: {word_count}\n")
                        f.write(f"{text}\n")
                        f.write(f"{'='*50}\n\n")
            else:
                # Fallback to text file
                with open(HISTORY_FILE, "r", encoding="utf-8") as src:
                    with open(file_path, "w", encoding="utf-8") as dst:
                        dst.write(src.read())
            
            messagebox.showinfo("Export", f"History exported successfully to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export history: {str(e)}")
    
    def load_model(self):
        """Load the selected Whisper model"""
        model_size = self.model_var.get()
        
        # Check if moviepy is available and warn if not
        if not MOVIEPY_AVAILABLE:
            messagebox.showwarning(
                "Missing Library", 
                "The moviepy library is not installed. Video files (.mp4, .avi, etc.) will not be supported.\n\n"
                "To enable video file support, install moviepy with:\n"
                "pip install moviepy"
            )
        
        # Update status
        self.status_label.configure(text=f"STATUS: LOADING {model_size.upper()} MODEL")
        self.root.update()
        
        try:
            # Load the model
            self.transcriptor = AudioTranscriptor(model_size)
            
            # Update status
            self.status_label.configure(text=f"STATUS: {model_size.upper()} MODEL LOADED")
            
            # Reset after 2 seconds
            self.root.after(2000, lambda: self.status_label.configure(text="STATUS: IDLE"))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {str(e)}")
            self.status_label.configure(text="STATUS: ERROR LOADING MODEL")
            
            # Reset after 2 seconds
            self.root.after(2000, lambda: self.status_label.configure(text="STATUS: IDLE"))
    
    def copy_latest(self):
        """Copy the latest transcription to clipboard"""
        if self.latest_transcription:
            pyperclip.copy(self.latest_transcription)
            self.status_label.configure(text="STATUS: COPIED TO CLIPBOARD")
            self.root.after(2000, lambda: self.status_label.configure(text="STATUS: IDLE"))

    def load_audio_file(self):
        """Load and transcribe an external audio file"""
        if not self.transcriptor:
            messagebox.showerror("Error", "Please load the model first!")
            return
            
        # Open file dialog to select audio file
        filetypes = (
            ('Audio files', '*.wav;*.mp3;*.m4a;*.ogg;*.mp4;*.mpeg;*.mpg;*.avi;*.mov'),
            ('All files', '*.*')
        )
        
        file_path = filedialog.askopenfilename(
            title='Select an audio file',
            initialdir='/',
            filetypes=filetypes
        )
        
        if not file_path:
            return  # User cancelled
            
        # Ask if user wants to process in segments
        use_segments = messagebox.askyesno(
            "Segmented Processing", 
            "Would you like to divide the audio into 4 segments for faster access to partial results?\n\n"
            "This will allow you to start reading the first part while the others are being processed."
        )
        
        if use_segments:
            self.process_audio_in_segments(file_path)
        else:
            # Create progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Transcribing Audio")
            progress_window.geometry("400x150")
            progress_window.configure(bg="black")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            # Get file name for reference
            file_name = os.path.basename(file_path)
            
            # Progress label
            file_label = ttk.Label(progress_window, 
                                text=f"File: {file_name}",
                                style="Cyberpunk.TLabel")
            file_label.pack(pady=10)
            
            status_label = ttk.Label(progress_window, 
                                    text="Initializing transcription...",
                                    style="Cyberpunk.TLabel")
            status_label.pack(pady=10)
            
            # Indeterminate progress bar
            progress_bar = ttk.Progressbar(progress_window, mode="indeterminate", length=350)
            progress_bar.pack(pady=10)
            progress_bar.start(15)  # Start animation
            
            # Update status
            self.status_label.configure(text="STATUS: TRANSCRIBING FILE")
            self.root.update()
            
            # Function to run transcription in a separate thread
            def transcribe_thread():
                result = ""
                error = None
                
                try:
                    # Use a larger model for file transcription if available
                    current_model = self.model_var.get()
                    
                    # Update status
                    status_label.config(text="Loading model...")
                    progress_window.update()
                    
                    if current_model in ["tiny", "base"] and messagebox.askyesno(
                        "Model Selection", 
                        "Would you like to use a larger model (medium) for better accuracy?\n"
                        "Note: This may take longer to process."
                    ):
                        # Temporarily load a larger model
                        status_label.config(text="Loading medium model...")
                        progress_window.update()
                        temp_transcriptor = AudioTranscriptor("medium")
                        
                        status_label.config(text="Transcribing audio (this may take a while)...")
                        progress_window.update()
                        result = temp_transcriptor.transcribe_file(file_path)
                        del temp_transcriptor
                    else:
                        # Use current model
                        status_label.config(text="Transcribing audio (this may take a while)...")
                        progress_window.update()
                        result = self.transcriptor.transcribe_file(file_path)
                        
                except Exception as e:
                    error = str(e)
                
                # Schedule UI updates on the main thread
                self.root.after(0, lambda: self.finish_transcription(result, file_name, error, progress_window))
            
            # Start transcription in a separate thread
            import threading
            threading.Thread(target=transcribe_thread, daemon=True).start()
    
    def process_audio_in_segments(self, file_path):
        """Process an audio file in 4 segments for faster partial results"""
        # Get file name for reference
        file_name = os.path.basename(file_path)
        
        # Create a dedicated window for segmented processing
        segment_window = tk.Toplevel(self.root)
        segment_window.title("Segmented Processing")
        segment_window.geometry("600x500")
        segment_window.configure(bg="black")
        segment_window.transient(self.root)
        
        # Header
        header_label = ttk.Label(segment_window, 
                               text=f"Processing: {file_name}",
                               style="Cyberpunk.TLabel")
        header_label.pack(pady=10)
        
        # Status frame
        status_frame = ttk.Frame(segment_window, style="Cyberpunk.TFrame")
        status_frame.pack(fill="x", pady=5, padx=20)
        
        # Overall progress
        overall_label = ttk.Label(status_frame, 
                                text="Overall Progress: 0/4 segments",
                                style="Cyberpunk.TLabel")
        overall_label.pack(pady=5)
        
        overall_progress = ttk.Progressbar(status_frame, length=550, maximum=4)
        overall_progress.pack(pady=5)
        
        # Current segment progress
        current_label = ttk.Label(status_frame, 
                                text="Current Segment: Preparing...",
                                style="Cyberpunk.TLabel")
        current_label.pack(pady=5)
        
        segment_progress = ttk.Progressbar(status_frame, length=550, mode="indeterminate")
        segment_progress.pack(pady=5)
        segment_progress.start(15)
        
        # Time estimation
        time_label = ttk.Label(status_frame, 
                             text="Estimated time remaining: Calculating...",
                             style="Cyberpunk.TLabel")
        time_label.pack(pady=5)
        
        # Results frame with scrollbar
        results_frame = ttk.Frame(segment_window, style="Cyberpunk.TFrame")
        results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Add scrollbar
        results_scrollbar = ttk.Scrollbar(results_frame)
        results_scrollbar.pack(side="right", fill="y")
        
        # Results text area
        results_text = scrolledtext.ScrolledText(results_frame,
                                              wrap="word",
                                              height=15,
                                              bg="black",
                                              fg="#00ff00",
                                              font=("Courier", 10),
                                              yscrollcommand=results_scrollbar.set)
        results_text.pack(fill="both", expand=True)
        results_scrollbar.config(command=results_text.yview)
        
        # Initial message
        results_text.insert("1.0", "Preparing to process audio in segments...\n")
        
        # Function to process segments in a separate thread
        def process_segments_thread():
            start_time = time.time()
            all_results = []
            error = None
            
            try:
                # Prepare the audio file
                results_text.insert("end", "Analyzing audio file...\n")
                segment_window.update()
                
                # Get audio duration and create segments
                audio_path, duration = self.prepare_audio_file(file_path)
                
                # Calculate segment duration
                segment_duration = duration / 4
                
                # Update UI
                results_text.insert("end", f"Audio duration: {duration:.2f} seconds\n")
                results_text.insert("end", f"Dividing into 4 segments of {segment_duration:.2f} seconds each\n\n")
                segment_window.update()
                
                # Process each segment
                for i in range(4):
                    # Update progress
                    segment_start = i * segment_duration
                    segment_end = (i + 1) * segment_duration if i < 3 else duration
                    
                    current_label.config(text=f"Current Segment: {i+1}/4 (Time: {segment_start:.2f}s - {segment_end:.2f}s)")
                    segment_window.update()
                    
                    # Extract segment
                    segment_file = self.extract_audio_segment(audio_path, segment_start, segment_end)
                    
                    # Transcribe segment
                    results_text.insert("end", f"[SEGMENT {i+1}/4] Transcribing...\n")
                    segment_window.update()
                    
                    # Calculate time estimation for remaining segments
                    if i > 0:
                        elapsed_time = time.time() - start_time
                        time_per_segment = elapsed_time / i
                        remaining_segments = 4 - i
                        estimated_time = time_per_segment * remaining_segments
                        
                        # Update time estimation
                        time_label.config(text=f"Estimated time remaining: {estimated_time:.1f} seconds")
                    
                    # Transcribe the segment
                    segment_result = self.transcriptor.transcribe_file(segment_file)
                    
                    # Add to results
                    all_results.append(segment_result)
                    
                    # Display segment result
                    results_text.insert("end", f"[SEGMENT {i+1}/4] Result:\n{segment_result}\n\n")
                    results_text.see("end")
                    
                    # Update progress
                    overall_progress["value"] = i + 1
                    segment_window.update()
                    
                    # Clean up segment file
                    try:
                        os.remove(segment_file)
                    except:
                        pass
                
                # Combine all results
                combined_result = " ".join(all_results)
                
                # Log the combined transcription
                self.log_transcription(f"[FILE: {file_name}]\n{combined_result}")
                
                # Store the latest transcription
                self.latest_transcription = combined_result
                
                # Update word count
                word_count = len(combined_result.split())
                self.word_count_label.configure(text=f"WORDS: {word_count}")
                
                # Enable copy and export buttons
                self.copy_button.configure(state="normal")
                self.export_button.configure(state="normal")
                
                # Display the result in the main window
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.output_text.insert("1.0", f"\n{'='*50}\n")
                self.output_text.insert("1.0", f"{combined_result}\n")
                self.output_text.insert("1.0", f"[FILE: {file_name}]\n")
                self.output_text.insert("1.0", f"[TIMESTAMP: {timestamp}]\n")
                self.output_text.insert("1.0", f"[FILE_TRANSCRIPTION_{timestamp.replace(':', '')}]\n")
                
                # Update final status
                current_label.config(text="Processing complete!")
                time_label.config(text=f"Total processing time: {time.time() - start_time:.1f} seconds")
                segment_progress.stop()
                segment_progress["mode"] = "determinate"
                segment_progress["value"] = 100
                
                # Add completion message
                results_text.insert("end", "\n==== PROCESSING COMPLETE ====\n")
                results_text.insert("end", f"Total processing time: {time.time() - start_time:.1f} seconds\n")
                results_text.insert("end", f"Total words: {word_count}\n")
                results_text.see("end")
                
            except Exception as e:
                error = str(e)
                results_text.insert("end", f"\nERROR: {error}\n")
                
                # Display error in main window
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.output_text.insert("1.0", f"\n{'='*50}\n")
                self.output_text.insert("1.0", f"Error processing file: {error}\n")
                self.output_text.insert("1.0", f"[FILE: {file_name}]\n")
                self.output_text.insert("1.0", f"[TIMESTAMP: {timestamp}]\n")
                self.output_text.insert("1.0", f"[ERROR]\n")
            
            # Reset status
            self.status_label.configure(text="STATUS: IDLE")
        
        # Start processing in a separate thread
        import threading
        threading.Thread(target=process_segments_thread, daemon=True).start()
    
    def prepare_audio_file(self, file_path):
        """Prepare audio file for segmented processing and return path and duration"""
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Process based on file type
        audio_formats = ['.wav', '.mp3', '.m4a', '.ogg']
        video_formats = ['.mp4', '.mpeg', '.mpg', '.avi', '.mov']
        
        if ext in video_formats:
            if not MOVIEPY_AVAILABLE:
                raise ImportError("The moviepy library is required to process video files.")
            
            try:
                # Try using ffmpeg directly first (more reliable for some video formats)
                import subprocess
                
                # Create a temporary file for the audio
                temp_audio = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                temp_audio.close()
                
                # Get duration using ffprobe
                duration_cmd = [
                    "ffprobe", 
                    "-v", "error", 
                    "-show_entries", "format=duration", 
                    "-of", "default=noprint_wrappers=1:nokey=1", 
                    file_path
                ]
                
                try:
                    duration = float(subprocess.check_output(duration_cmd).decode('utf-8').strip())
                except:
                    # Default duration if ffprobe fails
                    duration = 0
                
                # Extract audio using ffmpeg
                extract_cmd = [
                    "ffmpeg",
                    "-i", file_path,
                    "-q:a", "0",
                    "-map", "a",
                    "-y",  # Overwrite output file if it exists
                    temp_audio.name
                ]
                
                subprocess.run(extract_cmd, check=True, capture_output=True)
                
                # If we couldn't get duration from ffprobe, try to get it from the extracted audio
                if duration == 0:
                    audio = AudioFileClip(temp_audio.name)
                    duration = audio.duration
                    audio.close()
                
                return temp_audio.name, duration
                
            except Exception as e:
                print(f"FFmpeg extraction failed: {str(e)}")
                print("Falling back to moviepy...")
                
                # Fallback to moviepy
                try:
                    # Extract audio from video
                    video = VideoFileClip(file_path)
                    
                    # Check if audio is available
                    if video.audio is None:
                        video.close()
                        raise ValueError("No audio track found in the video file")
                    
                    # Get duration
                    duration = video.duration
                    
                    # Create a temporary file for the audio
                    temp_audio = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                    temp_audio.close()
                    
                    # Extract audio
                    video.audio.write_audiofile(temp_audio.name, verbose=False, logger=None)
                    video.close()
                    
                    return temp_audio.name, duration
                except Exception as e:
                    raise ValueError(f"Failed to extract audio from video: {str(e)}")
            
        elif ext in audio_formats:
            # Load audio file to get duration
            if ext == '.wav':
                with wave.open(file_path, 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration = frames / float(rate)
                return file_path, duration
            else:
                try:
                    # Try using ffprobe first
                    import subprocess
                    
                    duration_cmd = [
                        "ffprobe", 
                        "-v", "error", 
                        "-show_entries", "format=duration", 
                        "-of", "default=noprint_wrappers=1:nokey=1", 
                        file_path
                    ]
                    
                    duration = float(subprocess.check_output(duration_cmd).decode('utf-8').strip())
                    return file_path, duration
                    
                except Exception:
                    # Fallback to moviepy
                    if not MOVIEPY_AVAILABLE:
                        raise ImportError("The moviepy library is required to process this audio format.")
                    
                    audio = AudioFileClip(file_path)
                    duration = audio.duration
                    audio.close()
                    return file_path, duration
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def extract_audio_segment(self, audio_path, start_time, end_time):
        """Extract a segment of audio from the given file"""
        # Get file extension
        _, ext = os.path.splitext(audio_path)
        ext = ext.lower()
        
        # Create a temporary file for the segment
        temp_segment = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        temp_segment.close()
        
        try:
            # Try using ffmpeg first (more reliable)
            import subprocess
            
            extract_cmd = [
                "ffmpeg",
                "-i", audio_path,
                "-ss", str(start_time),
                "-to", str(end_time),
                "-q:a", "0",
                "-y",  # Overwrite output file if it exists
                temp_segment.name
            ]
            
            subprocess.run(extract_cmd, check=True, capture_output=True)
            return temp_segment.name
            
        except Exception as e:
            print(f"FFmpeg segment extraction failed: {str(e)}")
            print("Falling back to native methods...")
            
            # Fallback to native methods
            if ext == '.wav':
                # Use wave module for WAV files
                try:
                    with wave.open(audio_path, 'rb') as wf:
                        # Get file parameters
                        channels = wf.getnchannels()
                        sample_width = wf.getsampwidth()
                        framerate = wf.getframerate()
                        
                        # Calculate frame positions
                        start_frame = int(start_time * framerate)
                        end_frame = int(end_time * framerate)
                        
                        # Set position to start frame
                        wf.setpos(start_frame)
                        
                        # Read frames
                        frames = wf.readframes(end_frame - start_frame)
                        
                        # Write segment to new file
                        with wave.open(temp_segment.name, 'wb') as segment_file:
                            segment_file.setnchannels(channels)
                            segment_file.setsampwidth(sample_width)
                            segment_file.setframerate(framerate)
                            segment_file.writeframes(frames)
                    
                    return temp_segment.name
                except Exception as wave_error:
                    print(f"Wave extraction failed: {str(wave_error)}")
            
            # Last resort: try moviepy
            if MOVIEPY_AVAILABLE:
                try:
                    audio = AudioFileClip(audio_path)
                    segment = audio.subclip(start_time, end_time)
                    segment.write_audiofile(temp_segment.name, verbose=False, logger=None)
                    audio.close()
                    segment.close()
                    return temp_segment.name
                except Exception as moviepy_error:
                    raise ValueError(f"Failed to extract audio segment: {str(moviepy_error)}")
            else:
                raise ImportError("The moviepy library is required to process this audio format.")

    def finish_transcription(self, result, file_name, error, progress_window):
        """Complete the transcription process after the thread finishes"""
        # Close progress window
        progress_window.destroy()
        
        if error:
            # Handle error
            error_msg = f"Error transcribing file: {error}"
            messagebox.showerror("Transcription Error", error_msg)
            self.output_text.insert("1.0", f"\n{'='*50}\n")
            self.output_text.insert("1.0", f"{error_msg}\n")
            self.output_text.insert("1.0", f"[ERROR]\n")
        else:
            # Log the transcription with file reference
            self.log_transcription(f"[FILE: {file_name}]\n{result}")
            
            # Store the latest transcription
            self.latest_transcription = result
            
            # Update word count
            word_count = len(result.split())
            self.word_count_label.configure(text=f"WORDS: {word_count}")
            
            # Enable copy and export buttons
            self.copy_button.configure(state="normal")
            self.export_button.configure(state="normal")
            
            # Display the result with cyberpunk formatting
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.output_text.insert("1.0", f"\n{'='*50}\n")
            self.output_text.insert("1.0", f"{result}\n")
            self.output_text.insert("1.0", f"[FILE: {file_name}]\n")
            self.output_text.insert("1.0", f"[TIMESTAMP: {timestamp}]\n")
            self.output_text.insert("1.0", f"[FILE_TRANSCRIPTION_{timestamp.replace(':', '')}]\n")
        
        # Reset status
        self.status_label.configure(text="STATUS: IDLE")

    def batch_process_files(self):
        """Process multiple audio files in batch mode"""
        if not self.transcriptor:
            messagebox.showerror("Error", "Please load the model first!")
            return
            
        # Open file dialog to select multiple audio files
        filetypes = (
            ('Audio files', '*.wav;*.mp3;*.m4a;*.ogg;*.mp4;*.mpeg;*.mpg;*.avi;*.mov'),
            ('All files', '*.*')
        )
        
        file_paths = filedialog.askopenfilenames(
            title='Select audio files for batch processing',
            initialdir='/',
            filetypes=filetypes
        )
        
        if not file_paths or len(file_paths) == 0:
            return  # User cancelled
            
        # Ask if user wants to use a larger model
        use_larger_model = False
        current_model = self.model_var.get()
        if current_model in ["tiny", "base"] and messagebox.askyesno(
            "Model Selection", 
            "Would you like to use a larger model (medium) for better accuracy?\n"
            "Note: This may take longer to process."
        ):
            use_larger_model = True
        
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Batch Processing")
        progress_window.geometry("400x200")
        progress_window.configure(bg="black")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Progress label
        progress_label = ttk.Label(progress_window, 
                                 text="Processing files...",
                                 style="Cyberpunk.TLabel")
        progress_label.pack(pady=10)
        
        # Progress bar
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, 
                                     variable=progress_var,
                                     maximum=len(file_paths),
                                     length=350)
        progress_bar.pack(pady=10)
        
        # File counter label
        counter_label = ttk.Label(progress_window, 
                                text=f"File 0/{len(file_paths)}",
                                style="Cyberpunk.TLabel")
        counter_label.pack(pady=10)
        
        # Current file label
        current_file_label = ttk.Label(progress_window, 
                                     text="",
                                     style="Cyberpunk.TLabel")
        current_file_label.pack(pady=10)
        
        # Cancel button
        cancel_var = tk.BooleanVar(value=False)
        cancel_button = ttk.Button(progress_window,
                                 text="[CANCEL]",
                                 command=lambda: cancel_var.set(True),
                                 style="Cyberpunk.TButton")
        cancel_button.pack(pady=10)
        
        # Update the UI
        progress_window.update()
        
        # Function to run batch processing in a separate thread
        def batch_thread():
            batch_results = []
            temp_transcriptor = None
            
            try:
                # Initialize the larger model if needed
                if use_larger_model:
                    progress_label.config(text="Loading medium model...")
                    progress_window.update()
                    temp_transcriptor = AudioTranscriptor("medium")
                
                # Process each file
                for i, file_path in enumerate(file_paths):
                    # Check if cancelled
                    if cancel_var.get():
                        break
                        
                    # Update progress
                    file_name = os.path.basename(file_path)
                    progress_var.set(i)
                    counter_label.config(text=f"File {i+1}/{len(file_paths)}")
                    current_file_label.config(text=f"Processing: {file_name}")
                    progress_window.update()
                    
                    try:
                        # Transcribe the file
                        if use_larger_model:
                            result = temp_transcriptor.transcribe_file(file_path)
                        else:
                            result = self.transcriptor.transcribe_file(file_path)
                        
                        # Add to results
                        batch_results.append({
                            "file": file_name,
                            "path": file_path,
                            "text": result
                        })
                        
                        # Log the transcription
                        self.log_transcription(f"[BATCH FILE: {file_name}]\n{result}")
                        
                    except Exception as e:
                        error_msg = f"Error processing {file_name}: {str(e)}"
                        batch_results.append({
                            "file": file_name,
                            "path": file_path,
                            "text": f"[ERROR: {str(e)}]"
                        })
                        
                        # Show error but continue with next file
                        self.root.after(0, lambda err=error_msg: messagebox.showerror("Batch Processing Error", err))
            
            finally:
                # Clean up temporary transcriptor if used
                if temp_transcriptor:
                    del temp_transcriptor
                
                # Schedule UI updates on the main thread
                self.root.after(0, lambda: self.finish_batch_processing(batch_results, progress_window, cancel_var.get()))
        
        # Start batch processing in a separate thread
        import threading
        threading.Thread(target=batch_thread, daemon=True).start()
    
    def finish_batch_processing(self, batch_results, progress_window, was_cancelled):
        """Complete the batch processing after the thread finishes"""
        # Close progress window
        progress_window.destroy()
        
        if was_cancelled:
            messagebox.showinfo("Batch Processing", "Batch processing was cancelled.")
            return
            
        if not batch_results:
            messagebox.showinfo("Batch Processing", "No files were processed.")
            return
        
        # Display summary
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.output_text.insert("1.0", f"\n{'='*50}\n")
        self.output_text.insert("1.0", f"Processed {len(batch_results)} files\n")
        
        # Count successful transcriptions
        successful = sum(1 for r in batch_results if not r["text"].startswith("[ERROR:"))
        
        # Display the last result in the main window
        last_result = batch_results[-1]
        self.latest_transcription = last_result["text"]
        self.output_text.insert("1.0", f"{last_result['text']}\n")
        self.output_text.insert("1.0", f"[FILE: {last_result['file']}]\n")
        self.output_text.insert("1.0", f"[TIMESTAMP: {timestamp}]\n")
        self.output_text.insert("1.0", f"[BATCH_TRANSCRIPTION_{timestamp.replace(':', '')}]\n")
        
        # Update word count for the last file
        word_count = len(last_result["text"].split())
        self.word_count_label.configure(text=f"WORDS: {word_count}")
        
        # Enable copy and export buttons
        self.copy_button.configure(state="normal")
        self.export_button.configure(state="normal")
        
        # Show completion message
        messagebox.showinfo("Batch Processing Complete", 
                          f"Successfully processed {successful} of {len(batch_results)} files.")

    def export_transcription(self):
        """Export the latest transcription to various formats"""
        if not self.latest_transcription:
            messagebox.showerror("Error", "No transcription available to export!")
            return
            
        # Create export window
        export_window = tk.Toplevel(self.root)
        export_window.title("Export Transcription")
        export_window.geometry("400x300")
        export_window.configure(bg="black")
        
        # Format selection
        format_frame = ttk.Frame(export_window, style="Cyberpunk.TFrame")
        format_frame.pack(fill="x", pady=10, padx=20)
        
        ttk.Label(format_frame, 
                text="[SELECT FORMAT]:",
                style="Cyberpunk.TLabel").pack(side="left")
        
        format_var = tk.StringVar(value="txt")
        format_combo = ttk.Combobox(format_frame, 
                                  textvariable=format_var,
                                  values=["txt", "json", "srt"],
                                  state="readonly",
                                  width=10)
        format_combo.pack(side="left", padx=5)
        
        # Preview frame
        preview_frame = ttk.Frame(export_window, style="Cyberpunk.TFrame")
        preview_frame.pack(fill="both", expand=True, pady=10, padx=20)
        
        ttk.Label(preview_frame, 
                text="[PREVIEW]:",
                style="Cyberpunk.TLabel").pack(anchor="w")
        
        preview_text = scrolledtext.ScrolledText(preview_frame,
                                              wrap="word",
                                              height=10,
                                              bg="black",
                                              fg="#00ff00",
                                              font=("Courier", 10))
        preview_text.pack(fill="both", expand=True, pady=5)
        
        # Initial preview
        preview_text.insert("1.0", self.latest_transcription)
        
        # Update preview when format changes
        def update_preview(*args):
            preview_text.delete("1.0", "end")
            format_type = format_var.get()
            
            if format_type == "txt":
                preview_text.insert("1.0", self.latest_transcription)
            elif format_type == "json":
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                json_data = {
                    "timestamp": timestamp,
                    "text": self.latest_transcription,
                    "word_count": len(self.latest_transcription.split())
                }
                preview_text.insert("1.0", json.dumps(json_data, indent=2))
            elif format_type == "srt":
                preview_text.insert("1.0", self.create_srt_format(self.latest_transcription))
        
        format_var.trace("w", update_preview)
        
        # Export button
        export_button = ttk.Button(export_window,
                                 text="[EXPORT]",
                                 command=lambda: self.save_export(format_var.get()),
                                 style="Cyberpunk.TButton")
        export_button.pack(pady=10)
    
    def create_srt_format(self, text):
        """Convert text to SRT subtitle format"""
        lines = text.split('. ')
        srt_content = ""
        
        # Estimate about 3 seconds per sentence
        current_time = timedelta(seconds=0)
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            # Clean the line
            line = line.strip()
            if not line.endswith('.'):
                line += '.'
                
            # Calculate duration based on word count (approx. 0.3s per word)
            word_count = len(line.split())
            duration = max(1, word_count * 0.3)  # At least 1 second
            
            # Format timestamps
            start_time = current_time
            end_time = current_time + timedelta(seconds=duration)
            
            # Format: HH:MM:SS,mmm
            start_str = f"{int(start_time.total_seconds() // 3600):02d}:{int((start_time.total_seconds() % 3600) // 60):02d}:{int(start_time.total_seconds() % 60):02d},000"
            end_str = f"{int(end_time.total_seconds() // 3600):02d}:{int((end_time.total_seconds() % 3600) // 60):02d}:{int(end_time.total_seconds() % 60):02d},000"
            
            # Add entry
            srt_content += f"{i+1}\n{start_str} --> {end_str}\n{line}\n\n"
            
            # Update current time
            current_time = end_time
            
        return srt_content
    
    def save_export(self, format_type):
        """Save the exported transcription to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Default extension and content
        extension = ".txt"
        content = self.latest_transcription
        
        if format_type == "json":
            extension = ".json"
            json_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "text": self.latest_transcription,
                "word_count": len(self.latest_transcription.split())
            }
            content = json.dumps(json_data, indent=2)
        elif format_type == "srt":
            extension = ".srt"
            content = self.create_srt_format(self.latest_transcription)
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[("All Files", "*.*")],
            initialfile=f"transcription_{timestamp}{extension}"
        )
        
        if not file_path:
            return  # User cancelled
            
        # Save the file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Export Successful", f"Transcription exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Error saving file: {str(e)}")

class AudioTranscriptor:
    def __init__(self, model_size="base"):
        self.model = whisper.load_model(model_size)
        self.model_size = model_size
        self.temp_files = []

    def __del__(self):
        """Clean up any temporary files when the object is destroyed"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass

    def transcribe_file(self, audio_path):
        try:
            # Check if file exists
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
                
            # Get file extension
            _, ext = os.path.splitext(audio_path)
            ext = ext.lower()
            
            # Process based on file type
            audio_formats = ['.wav', '.mp3', '.m4a', '.ogg']
            video_formats = ['.mp4', '.mpeg', '.mpg', '.avi', '.mov']
            supported_formats = audio_formats + video_formats
            
            if ext not in supported_formats:
                raise ValueError(f"Unsupported audio format: {ext}. Supported formats: {', '.join(supported_formats)}")
            
            # If it's a video file, extract the audio first
            processed_audio_path = audio_path
            if ext in video_formats:
                if not MOVIEPY_AVAILABLE:
                    raise ImportError("The moviepy library is required to process video files. "
                                     "Please install it with 'pip install moviepy'.")
                
                # Extract audio from video
                processed_audio_path = self._extract_audio_from_video(audio_path)
            
            # Transcribe with appropriate options based on model size
            options = {}
            
            # For larger models, use more features
            if self.model_size in ["medium", "large"]:
                options = {
                    "language": "en",  # Auto-detect language
                    "task": "transcribe",
                    "fp16": False  # Use FP16 for faster processing if available
                }
            
            # Perform transcription
            result = self.model.transcribe(processed_audio_path, **options)
            return result["text"]
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            return f"[ERROR: {str(e)}]"
    
    def _extract_audio_from_video(self, video_path):
        """Extract audio from a video file and return the path to the audio file"""
        # Create a temporary file for the audio
        temp_audio = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_audio.close()
        
        # Add to list of temp files to clean up later
        self.temp_files.append(temp_audio.name)
        
        try:
            # Extract audio using moviepy
            video = VideoFileClip(video_path)
            
            # Check if audio is available
            if video.audio is None:
                video.close()
                raise ValueError("No audio track found in the video file")
                
            # Write audio to file with verbose=False to suppress output
            video.audio.write_audiofile(temp_audio.name, verbose=False, logger=None)
            video.close()
            
            return temp_audio.name
        except Exception as e:
            # If there's an error with moviepy, try using ffmpeg directly
            print(f"Error using moviepy: {str(e)}")
            print("Trying alternative method with ffmpeg...")
            
            import subprocess
            try:
                # Use ffmpeg directly
                subprocess.run([
                    "ffmpeg", "-i", video_path, 
                    "-q:a", "0", "-map", "a", temp_audio.name
                ], check=True, capture_output=True)
                
                return temp_audio.name
            except Exception as ffmpeg_error:
                print(f"Error using ffmpeg: {str(ffmpeg_error)}")
                raise ValueError(f"Failed to extract audio from video: {str(e)}")

def main():
    root = tk.Tk()
    app = TranscriptorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 