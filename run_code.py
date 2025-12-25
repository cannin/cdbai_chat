import argparse
import json
import logging
import os
from dotenv import load_dotenv

from cdbai.pipeline import cdbai_chat

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the cdbai_chat pipeline.")
    parser.add_argument("-p", "--prompt", required=True, help="User prompt describing the desired analysis.")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Print the loaded environment variables and run with DEBUG logging.",
    )
    args = parser.parse_args()

    log_level = "DEBUG" if args.debug else os.environ.get("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.debug:
        env_snapshot = {key: value for key, value in sorted(os.environ.items())}
        print("Loaded environment variables:")
        print(json.dumps(env_snapshot, indent=2, sort_keys=True))

    result = cdbai_chat(args.prompt)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
