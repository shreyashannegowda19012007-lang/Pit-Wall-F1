"""
Pitwall F1 - Unified Application Launcher
==========================================
Launches the consolidated Formula One Pit-Wall Race Engineering Platform.
- Development mode (default): Launches FastAPI backend on port 8000 and Vite frontend on port 5173 with proxy.
- Production mode (--prod): Launches single-origin FastAPI server on port 8000 serving built React SPA and API.
"""

import sys
import os
import subprocess
import argparse
import signal
import time

def main():
    parser = argparse.ArgumentParser(description="Pitwall F1 Unified Application Launcher")
    parser.add_argument("--prod", action="store_true", help="Run in production mode (FastAPI serving built React SPA)")
    parser.add_argument("--port", type=int, default=8000, help="Backend port (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Backend host (default: 127.0.0.1)")
    args = parser.parse_args()

    root_dir = os.path.abspath(os.path.dirname(__file__))

    if args.prod:
        # Verify frontend build exists
        frontend_dist = os.path.join(root_dir, "frontend", "dist")
        if not os.path.exists(frontend_dist) or not os.path.exists(os.path.join(frontend_dist, "index.html")):
            print("[INFO] Building frontend production bundle...")
            subprocess.run(["npm", "--prefix", "frontend", "run", "build"], cwd=root_dir, check=True, shell=True)

        print(f"\n=======================================================")
        print(f"  PITWALL F1 UNIFIED PLATFORM (PRODUCTION)")
        print(f"  Single Origin: http://{args.host}:{args.port}")
        print(f"=======================================================\n")
        cmd = [sys.executable, "-m", "uvicorn", "src.main_api:app", "--host", args.host, "--port", str(args.port)]
        subprocess.run(cmd, cwd=root_dir)
    else:
        print(f"\n=======================================================")
        print(f"  PITWALL F1 UNIFIED PLATFORM (DEVELOPMENT)")
        print(f"  Primary Application URL: http://localhost:5173/app")
        print(f"  Backend API URL:         http://{args.host}:{args.port}/api")
        print(f"=======================================================\n")

        # Start FastAPI backend process
        api_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.main_api:app", "--host", args.host, "--port", str(args.port)],
            cwd=root_dir
        )

        time.sleep(1.5)

        # Start Vite frontend process
        try:
            vite_proc = subprocess.Popen(
                ["npm", "--prefix", "frontend", "run", "dev", "--", "--host"],
                cwd=root_dir,
                shell=True
            )
            api_proc.wait()
        except KeyboardInterrupt:
            print("\nShutting down Pitwall F1 Platform...")
            api_proc.terminate()
            if 'vite_proc' in locals():
                vite_proc.terminate()

if __name__ == "__main__":
    main()
