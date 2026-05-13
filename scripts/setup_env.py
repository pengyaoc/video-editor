import os
import sys
import shutil
import subprocess

VENV_DIR = os.path.expanduser("~/.cache/video-editor/venv")
REQUIRED_PACKAGES = ["faster-whisper"]


def check_prerequisites():
    if shutil.which("ffmpeg") is None:
        print("Error: FFmpeg not found.")
        print("  macOS:  brew install ffmpeg")
        print("  Linux:  apt install ffmpeg")
        sys.exit(1)


def ensure_venv():
    venv_python = os.path.join(VENV_DIR, "bin", "python3")

    if os.path.exists(venv_python):
        return venv_python

    print(f"First run: creating virtual environment at {VENV_DIR}...")
    subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)

    print("Installing dependencies...")
    pip = os.path.join(VENV_DIR, "bin", "pip")
    subprocess.run(
        [pip, "install", "--quiet"] + REQUIRED_PACKAGES,
        check=True,
    )
    print("Environment ready.")
    return venv_python


def activate():
    """Ensure venv exists and re-exec the calling script under the venv Python if needed."""
    check_prerequisites()
    venv_python = ensure_venv()

    # Already running inside the venv (check sys.prefix instead of executable in case of symlinks)
    if os.path.normpath(sys.prefix) == os.path.normpath(VENV_DIR):
        return

    # Re-exec the calling script under the venv Python
    os.execv(venv_python, [venv_python] + sys.argv)
