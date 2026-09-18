from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

API_HOST = "127.0.0.1"
API_PORT = "8000"

UI_HOST = "127.0.0.1"
UI_PORT = "8501"


def start_process(command: list[str]) -> subprocess.Popen:
    """
    Start a child process from the project root.
    """
    return subprocess.Popen(
        command,
        cwd=PROJECT_ROOT,
    )


def terminate_process(process: subprocess.Popen) -> None:
    """
    Terminate a child process cleanly.
    """
    if process.poll() is None:
        process.terminate()

        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def main() -> None:
    print("=" * 60)
    print("DotMappers AI Support Ticket Intelligence")
    print("=" * 60)
    print()

    api_process = None
    ui_process = None

    try:
        print("Starting FastAPI backend...")
        api_process = start_process(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                API_HOST,
                "--port",
                API_PORT,
            ]
        )

        # Give FastAPI a moment to start before launching Streamlit.
        time.sleep(2)

        print("Starting Streamlit UI...")
        ui_process = start_process(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(PROJECT_ROOT / "ui" / "streamlit_app.py"),
                "--server.address",
                UI_HOST,
                "--server.port",
                str(UI_PORT),
            ]
        )

        print()
        print("Application started successfully.")
        print()
        print(f"FastAPI : http://{API_HOST}:{API_PORT}")
        print(f"Swagger : http://{API_HOST}:{API_PORT}/docs")
        print(f"Streamlit: http://{UI_HOST}:{UI_PORT}")
        print()
        print("Ollama must be running separately on port 11434.")
        print("Press Ctrl+C to stop the application.")
        print()

        while True:
            # If either application exits unexpectedly, stop everything.
            if api_process.poll() is not None:
                print("FastAPI process stopped.")
                break

            if ui_process.poll() is not None:
                print("Streamlit process stopped.")
                break

            time.sleep(1)

    except KeyboardInterrupt:
        print()
        print("Stopping application...")

    finally:
        if ui_process is not None:
            terminate_process(ui_process)

        if api_process is not None:
            terminate_process(api_process)

        print("Application stopped.")


if __name__ == "__main__":
    main()
