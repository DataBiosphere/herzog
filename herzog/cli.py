import os
import sys
import json
import argparse
from contextlib import closing
from typing import List, Optional

import herzog


def forward(cli_args: Optional[List[str]] = None):
    """Convert Herzog formatted Python scripts to iPython .ipynb files."""
    parser = argparse.ArgumentParser(prog="Herzog", description=forward.__doc__)
    parser.add_argument("input", nargs="?", help="filepath of herzog-formatted Python script.")
    parser.add_argument("-", dest="from_stdin", action="store_true", help="Read input from 'stdin'")
    parser.add_argument("--output", "-o", help="If set, write output to file")
    args = parser.parse_args(cli_args)
    fh = sys.stdin if args.from_stdin else open(args.input)
    with closing(fh):
        out = json.dumps(herzog.translate_to_ipynb(fh), indent=2)
        if args.output:
            with open(args.output, "wb") as fh_out:
                fh_out.write(out.encode("utf-8"))
        else:
            print(out)

def backward(cli_args: Optional[List[str]] = None):
    """Convert iPython .ipynb files to Herzog formatted Python scripts."""
    parser = argparse.ArgumentParser(prog="Herzog", description=backward.__doc__)
    parser.add_argument("input", nargs="?", help="filepath of iPython .ipynb file.")
    parser.add_argument("-", dest="from_stdin", action="store_true", help="Read input from 'stdin'")
    parser.add_argument("--output", "-o", help="If set, write output to file")
    args = parser.parse_args(cli_args)
    fh = sys.stdin if args.from_stdin else open(args.input)
    with closing(fh):
        out = "".join([line for line in herzog.translate_to_herzog(fh)])
        if args.output:
            with open(args.output, "w") as fh_out:
                fh_out.write(out)
        else:
            print(out)
