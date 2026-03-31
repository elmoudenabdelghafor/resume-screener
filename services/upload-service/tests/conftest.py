import sys, pathlib
# Add the service root (parent of tests/) to sys.path so pytest can import main, worker, schemas etc.
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
