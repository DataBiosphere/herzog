import os
import sys
import json
import argparse
from typing import List, Optional

import herzog


def main(args: Optional[List[str]] = None):
    if args is None:
        args = sys.argv[1:]

    if len(args) == 1 and args[0] not in ("--help", "-h", "--version", "-v"):
        # maintain backwards compatibility
        with open(args[0]) as fh:
            print(json.dumps(herzog.translate_to_ipynb(fh), indent=2))
            exit()

    parser = argparse.ArgumentParser(prog="Herzog",
                                     description="Convert Herzog formatted Python scripting to "
                                                 "iPython .ipynb files, and back again.")
    subparser = parser.add_subparsers()
    convert = subparser.add_parser("convert")
    convert.add_argument("--input", "-i", type=str, required=True,
                         help="The name of an input file.  Type will be inferred by the extension "
                              "('.ipynb' or '.py').")
    convert.add_argument("--output", "-o", type=str, required=False, default=None,
                         help="The name of an output file.  Type will be inferred by the extension "
                              "('.ipynb' or '.py').  The type must not be the same as the input type.  "
                              "If this is not specified, output will be printed to stdout.")
    options = parser.parse_args(args)

    assert os.path.exists(options.input)

    with open(options.input, "r") as r:
        if options.input.endswith(".py") and (options.output.endswith(".ipynb") or options.output is None):
            output_file_contents = json.dumps(herzog.translate_to_ipynb(r), indent=2)
        elif options.input.endswith(".ipynb") and (options.output.endswith(".py") or options.output is None):
            output_file_contents = "".join([line for line in herzog.translate_to_herzog(r)])
        else:
            raise NotImplementedError(
                f"File types for input and output are not supported and/or compatible "
                f"(must be .py -> .ipynb or vice versa).\nInput: {options.input}\nOutput: {options.output}")

    if options.output:
        with open(options.output, "w") as w:
            w.write(output_file_contents)
    else:
        print(output_file_contents)
