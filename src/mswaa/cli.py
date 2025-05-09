from __future__ import annotations

import argparse
import logging
import signal
import sys

from . import ScrollAccelerator, common


def _timeout_handler(*_args):
    logging.info("Timeout")
    sys.exit(0)


def _init_logging(verbose: int = 0):
    logging.basicConfig(
        level=max(1, logging.WARNING - verbose * 10),
        format="%(asctime)s %(levelname)s: %(message)s",
    )


def main():
    arg_parser = argparse.ArgumentParser(common.app_name_human)
    arg_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="logging level. can be given multiple times",
    )
    arg_parser.add_argument(
        "--multiplier",
        type=float,
        default=None,
        help="Linear factor, default 1.",
    )
    arg_parser.add_argument(
        "--exp",
        type=float,
        default=None,
        help="Exponential factor. Try 1 or so.",
    )
    arg_parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="If set, will only trigger acceleration if the velocity is above this threshold.",
    )
    arg_parser.add_argument(
        "--timeout",
        type=int,
        help="Will quit after this time (secs). For debugging.",
    )
    args = arg_parser.parse_args()
    if common.config_fn.exists():
        config_env = {}
        code = compile(common.config_fn.read_text(), common.config_fn, "exec")
        exec(code, config_env, config_env)
        _init_logging(args.verbose or config_env.get("verbose", 0))
        logging.info(f"Loaded config {common.config_fn}")
        for key, value in args.__dict__.items():
            if value is None and key in config_env:
                args.__dict__[key] = config_env[key]
                logging.info(f"Use config setting {key} = {config_env[key]}")
    else:
        _init_logging(args.verbose)
        logging.warning(f"Config {common.config_fn} not found")
    if args.multiplier is None and args.exp is None:
        arg_parser.print_help()
        print()
        logging.error("Specify --multiplier and/or --exp.")
        sys.exit(1)
    if args.multiplier is None:
        args.multiplier = 1.0
    if args.exp is None:
        args.exp = 0.0
    if args.threshold is None:
        args.threshold = 0.0
    if args.timeout:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(args.timeout)
    app = ScrollAccelerator(
        multiplier=args.multiplier,
        exp=args.exp,
        threshold=args.threshold,
    )
    app.join()
