import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List

from clawhunt.config import find_node, find_venv_python


def start_backend(root: Path, python_exe: str, config: Dict) -> subprocess.Popen:
    backend_config = config["services"]["backend"]
    backend_dir = root / config["paths"]["backend_dir"]
    port, host = backend_config["port"], backend_config["host"]
    reload_flag = "--reload" if backend_config.get("reload", True) else ""

    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_dir) + os.pathsep + env.get("PYTHONPATH", "")

    cmd = [python_exe, "-m", "uvicorn", "app.main:app", "--host", host, "--port", str(port)]
    if reload_flag:
        cmd.append(reload_flag)

    print(f"[INFO] Starting backend on http://{host}:{port}")
    print(f"[INFO] Working directory: {backend_dir}")
    print(f"[INFO] Command: {' '.join(cmd)}")

    return subprocess.Popen(cmd, cwd=backend_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")


def start_frontend(root: Path, node_exe: str, config: Dict) -> subprocess.Popen:
    frontend_config = config["services"]["frontend"]
    frontend_dir = root / config["paths"]["frontend_dir"]
    port, host = frontend_config["port"], frontend_config["host"]

    env = os.environ.copy()
    node_dir = str(Path(node_exe).parent)
    env["Path"] = node_dir + os.pathsep + env.get("Path", "")
    env["PORT"] = str(port)

    npm_path = Path(node_dir) / "npm"
    if not npm_path.exists():
        npm_path = Path(node_dir) / "npm.cmd"
    cmd = [str(npm_path), "run", "dev"]

    print(f"[INFO] Starting frontend on http://{host}:{port}")
    print(f"[INFO] Working directory: {frontend_dir}")
    print(f"[INFO] Command: {' '.join(cmd)}")

    return subprocess.Popen(cmd, cwd=frontend_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")


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
                if line := proc.stdout.readline():
                    print(f"[{Path(proc.args[0]).name}] {line.strip()}")
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


def start_services(mode: str, root: Path, config: Dict) -> None:
    processes: List[subprocess.Popen] = []

    if mode in ["backend", "all"]:
        python_exe = find_venv_python(root, config) or sys.executable
        print(f"[INFO] Using Python: {python_exe}")
        processes.append(start_backend(root, python_exe, config))

    if mode in ["frontend", "all"]:
        node_exe = find_node()
        print(f"[INFO] Using Node: {node_exe}")
        processes.append(start_frontend(root, node_exe, config))

    if processes:
        monitor_processes(processes)
    else:
        print("[ERROR] No services to start")
        sys.exit(1)