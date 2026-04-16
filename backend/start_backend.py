"""
ReviewSense Analytics — Backend Startup Script
================================================
Run:  python start_backend.py
This is invoked automatically by the root-level `npm run dev:backend`.
"""

import os
import sys
import signal
import socket
import subprocess
import time

# ── Configuration ──────────────────────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 8000
RELOAD = True

# Ensure the project root is on sys.path so that
# `backend.app.main:app` resolves correctly regardless of cwd.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def is_port_in_use(port: int) -> bool:
    """Check whether a TCP port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True


def kill_port(port: int) -> None:
    """Best-effort kill of any process occupying *port* (Windows + Unix)."""
    if not is_port_in_use(port):
        return
    print(f"[*] Port {port} is busy - attempting to free it...")
    try:
        if sys.platform == "win32":
            # Use netstat + taskkill on Windows
            result = subprocess.run(
                ["netstat", "-ano", "-p", "TCP"],
                capture_output=True, text=True,
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 5 and f":{port}" in parts[1] and parts[3] == "LISTENING":
                    pid = parts[4]
                    subprocess.run(
                        ["taskkill", "/F", "/PID", pid],
                        capture_output=True,
                    )
                    print(f"   Killed PID {pid} on port {port}")
        else:
            # Unix / macOS
            subprocess.run(
                ["fuser", "-k", f"{port}/tcp"],
                capture_output=True,
            )
        time.sleep(0.5)
    except Exception as exc:
        print(f"   Could not kill port {port}: {exc}")


def main() -> None:
    print()
    print("=" * 58)
    print("  ReviewSense Analytics - Backend Launcher")
    print("=" * 58)
    print()

    # ── Port cleanup ──────────────────────────────────────
    kill_port(PORT)

    if is_port_in_use(PORT):
        print(f"[ERROR] Port {PORT} is still occupied after cleanup. Aborting.")
        print(f"   Manually free it and retry.")
        sys.exit(1)

    # ── Launch uvicorn ────────────────────────────────────
    print(f"[*] Starting FastAPI via uvicorn...")
    print(f"   Host:   {HOST}")
    print(f"   Port:   {PORT}")
    print(f"   Reload: {RELOAD}")
    print(f"   CWD:    {PROJECT_ROOT}")
    print()

    try:
        import uvicorn
        print(f"[SUCCESS] Backend running on http://localhost:{PORT}")
        print(f"   Docs:   http://localhost:{PORT}/docs")
        print(f"   Health: http://localhost:{PORT}/health")
        print()
        uvicorn.run(
            "backend.app.main:app",
            host=HOST,
            port=PORT,
            reload=RELOAD,
            reload_dirs=[os.path.join(PROJECT_ROOT, "backend")],
            log_level="info",
        )
    except ImportError:
        print("[ERROR] uvicorn is not installed.")
        print("   Run:  pip install uvicorn[standard]")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Backend stopped by user.")
    except Exception as exc:
        print(f"\n[ERROR] Backend crashed: {exc}")
        print("   Check the traceback above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
