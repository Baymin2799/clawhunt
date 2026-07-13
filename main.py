import argparse
from pathlib import Path

from clawhunt.config import load_config, load_env, setup_environment
from clawhunt.services import start_services


def main() -> None:
    parser = argparse.ArgumentParser(description="ClawHunt Service Manager")
    parser.add_argument("--mode", choices=["backend", "frontend", "all"], default="all")
    parser.add_argument("--config", type=str, default="config.json")
    parser.add_argument("--env-file", type=str, default=None)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    print(f"[INFO] Project root: {root}")

    config = load_config(root / args.config)
    env_file = args.env_file or config["paths"]["env_file"]
    load_env(root / env_file)
    setup_environment(config, root)

    start_services(args.mode, root, config)


if __name__ == "__main__":
    main()