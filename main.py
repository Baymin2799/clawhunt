import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


def load_env(env_path: Path) -> None:
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def find_venv_python(root: Path) -> Optional[str]:
    venv_paths = [
        root / "backend" / ".venv" / "Scripts" / "python.exe",
        root / "backend" / ".venv" / "bin" / "python",
        root / ".venv" / "Scripts" / "python.exe",
        root / ".venv" / "bin" / "python",
    ]
    for path in venv_paths:
        if path.exists():
            return str(path)
    return None


def find_node(root: Path) -> Optional[str]:
    node_paths = [
        root / ".tools" / "node-v22.23.1-win-x64" / "node.exe",
        root / ".tools" / "node-v22.23.1-win-x64" / "node",
    ]
    for path in node_paths:
        if path.exists():
            return str(path)
    return "node"


def start_backend(root: Path, python_exe: str, port: int = 8001) -> subprocess.Popen:
    backend_dir = root / "backend"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_dir) + os.pathsep + env.get("PYTHONPATH", "")

    cmd = [
        python_exe,
        "-m", "uvicorn",
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", str(port),
        "--reload",
    ]

    print(f"[INFO] Starting backend on http://127.0.0.1:{port}")
    print(f"[INFO] Working directory: {backend_dir}")
    print(f"[INFO] Command: {' '.join(cmd)}")

    return subprocess.Popen(
        cmd,
        cwd=backend_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def start_frontend(root: Path, node_exe: str, port: int = 5173) -> subprocess.Popen:
    frontend_dir = root / "clawhunt"
    env = os.environ.copy()
    env["PORT"] = str(port)

    cmd = [node_exe, "node_modules", ".bin", "vite", "--host", "127.0.0.1", "--port", str(port)]

    print(f"[INFO] Starting frontend on http://127.0.0.1:{port}")
    print(f"[INFO] Working directory: {frontend_dir}")
    print(f"[INFO] Command: {' '.join(cmd)}")

    return subprocess.Popen(
        cmd,
        cwd=frontend_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def start_frontend_with_npm(root: Path, node_exe: str) -> subprocess.Popen:
    frontend_dir = root / "clawhunt"
    env = os.environ.copy()
    env["Path"] = str(Path(node_exe).parent) + os.pathsep + env.get("Path", "")

    cmd = [node_exe, "-e", "require('vite').createServer({ server: { host: '127.0.0.1', port: 5173 } }).then(s => s.listen())"]

    print(f"[INFO] Starting frontend (npm run dev)")
    print(f"[INFO] Working directory: {frontend_dir}")

    return subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def monitor_processes(processes: List[subprocess.Popen]) -> None:
    print("\n[INFO] Services started. Press Ctrl+C to stop all services.\n")

    try:
        while True:
            for proc in processes:
                if proc.poll() is not None:
                    print(f"[ERROR] Process exited with code {proc.returncode}")
                    for line in proc.stdout:
                        print(line.strip())
                    sys.exit(1)

                line = proc.stdout.readline()
                if line:
                    print(f"[{proc.args[0]}] {line.strip()}")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[INFO] Stopping all services...")
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()
        print("[INFO] All services stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="ClawHunt Service Manager")
    parser.add_argument(
        "--mode",
        choices=["backend", "frontend", "all"],
        default="all",
        help="Which services to start (default: all)",
    )
    parser.add_argument(
        "--backend-port",
        type=int,
        default=8001,
        help="Backend service port (default: 8001)",
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=5173,
        help="Frontend service port (default: 5173)",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env.local",
        help="Path to environment file (default: .env.local)",
    )

    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    print(f"[INFO] Project root: {root}")

    env_path = root / args.env_file
    load_env(env_path)
    print(f"[INFO] Loaded environment from: {env_path}")

    processes: List[subprocess.Popen] = []

    if args.mode in ["backend", "all"]:
        python_exe = find_venv_python(root)
        if not python_exe:
            print("[WARNING] Virtual environment not found, using system Python")
            python_exe = sys.executable

        print(f"[INFO] Using Python: {python_exe}")
        proc = start_backend(root, python_exe, args.backend_port)
        processes.append(proc)

    if args.mode in ["frontend", "all"]:
        node_exe = find_node(root)
        print(f"[INFO] Using Node: {node_exe}")
        proc = start_frontend_with_npm(root, node_exe)
        processes.append(proc)

    if processes:
        monitor_processes(processes)
    else:
        print("[ERROR] No services to start")
        sys.exit(1)


if __name__ == "__main__":
    main()