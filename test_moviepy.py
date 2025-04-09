import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    import moviepy
    print(f"Moviepy version: {moviepy.__version__}")
    print("Moviepy is properly installed!")
    
    # Test video file handling
    from moviepy.editor import VideoFileClip
    print("VideoFileClip class is available")
    
except ImportError as e:
    print(f"Error importing moviepy: {e}")
    print("Please install moviepy with: pip install moviepy") 