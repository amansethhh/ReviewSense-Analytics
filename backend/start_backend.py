"""
ReviewSense Analytics — Backend Startup Script
================================================
Run:  python start_backend.py          (from any directory)
      npm run dev:backend              (from project root)
      npm start                        (full stack)

Key design decision
-------------------
os.chdir() and sys.path modification happen at MODULE LEVEL, before
main() is called. This is critical because uvicorn's watchfiles reloader
forks a new subprocess that re-executes THIS file's module scope — so the
CWD must be set here, not inside main(), or the reloader subprocess will
fail to import 'app.main'.
"""

import os
import sys
import socket
import subprocess
import time

# ── Resolve directories ─────────────────────────────────────────────────────
# This file lives at:  <project_root>/backend/start_backend.py
BACKEND_DIR  = os.path.dirname(os.path.abspath(__file__))   # .../backend
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)                  # .../ReviewSense-Analytics

# Change CWD to backend/ immediately so that uvicorn (and every subprocess it
# spawns via multiprocessing) resolves `from app.X import ...` correctly.
os.chdir(BACKEND_DIR)

# Also add backend/ to sys.path for in-process imports.
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ── Configuration ───────────────────────────────────────────────────────────
HOST   = "0.0.0.0"
PORT   = 8000
RELOAD = True


# ── Helpers ─────────────────────────────────────────────────────────────────

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
            result = subprocess.run(
                ["netstat", "-ano", "-p", "TCP"],
                capture_output=True, text=True,
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 5 and f":{port}" in parts[1] and parts[3] == "LISTENING":
                    pid = parts[4]
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                    print(f"   Killed PID {pid} on port {port}")
        else:
            subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
        time.sleep(0.5)
    except Exception as exc:
        print(f"   Could not kill port {port}: {exc}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("=" * 58)
    print("  ReviewSense Analytics - Backend Launcher")
    print("=" * 58)
    print()

    # Port cleanup
    kill_port(PORT)
    if is_port_in_use(PORT):
        print(f"[ERROR] Port {PORT} is still occupied. Aborting.")
        sys.exit(1)

    # Launch uvicorn
    print(f"[*] Starting FastAPI via uvicorn...")
    print(f"   Host:    {HOST}")
    print(f"   Port:    {PORT}")
    print(f"   Reload:  {RELOAD}")
    print(f"   CWD:     {BACKEND_DIR}")
    print()

    try:
        import uvicorn
        print(f"[SUCCESS] Backend running at http://localhost:{PORT}")
        print(f"   API Docs: http://localhost:{PORT}/docs")
        print(f"   Health:   http://localhost:{PORT}/health")
        print()
        uvicorn.run(
            "app.main:app",
            host=HOST,
            port=PORT,
            reload=RELOAD,
            reload_dirs=[BACKEND_DIR],
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
        sys.exit(1)


if __name__ == "__main__":
    main()
