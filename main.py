import sys
import os
import tempfile

from src.app import TrayApp

LOCK_FILE = os.path.join(tempfile.gettempdir(), "self_remembering_app.lock")

def single_instance():
    if sys.platform == "win32":
        import msvcrt
        try:
            fp = open(LOCK_FILE, "w")
            msvcrt.locking(fp.fileno(), msvcrt.LK_NBLCK, 1)
            return fp
        except (IOError, OSError):
            return None
    else:
        import fcntl
        try:
            fp = open(LOCK_FILE, "w")
            fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fp
        except (IOError, OSError):
            return None

def main():
    lock = single_instance()
    if lock is None:
        print("Already running.")
        sys.exit(0)
    app = TrayApp()
    app.run()

if __name__ == "__main__":
    main()
