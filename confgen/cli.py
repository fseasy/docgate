#!/usr/bin/env python3

import argparse
from typing import get_args

from docgate_confgen.data_types import EnvT
from docgate_confgen.gen import main as gen_main


def main() -> None:
  parser = argparse.ArgumentParser(description="The unified config/env generator for all modules")
  parser.add_argument("--env", "-e", required=True, choices=get_args(EnvT), help="generate which env")
  args = parser.parse_args()

  gen_main(args.env)
  print("===> Finished.")


if __name__ == "__main__":
  main()
