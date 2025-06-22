import sys
import os

# This is the crucial change.
# We add the 'src' directory to Python's path so it can find the 'app' module.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
import glob

# Create an instance of the Flask application using our factory function
app = create_app()

if __name__ == '__main__':
    # The glob path needs to be updated to look inside the 'src' directory.
    extra_dirs = ['content/'] # This is now relative to run.py's location
    extra_files = extra_dirs[:]
    for extra_dir in extra_dirs:
        extra_files.extend(glob.glob(extra_dir + '**/*.yaml', recursive=True))

    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=True,
        extra_files=extra_files
    )