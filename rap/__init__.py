
__version__ = '0.1dev'

import argparse
import re

from rap.processing_unit import ProcessingUnit
from rap.program import Program, ProgramError


input_pair_regex = re.compile("^\s*([a-zA-Z0-9]+)\s*:\s*([0-9]+)\s*$")

def parse_input(string, sep=',', pair_regex=input_pair_regex):
    registers = {}
    for pair in string.split(','):
        if not pair.strip():
            continue
        match = pair_regex.match(pair)
        if not match:
            raise ValueError('ass')
        register, value = match.groups()
        registers[register] = int(value)
    return registers



def make_parser():
    # TODO: Add help and description strings.
    parser = argparse.ArgumentParser('rap')
    parser.add_argument('file', type=argparse.FileType('r'))
    parser.add_argument('-i', '--input', metavar='input', type=parse_input)
    parser.add_argument('-o', '--output', metavar='format', nargs='?')
    parser.add_argument('-t', '--trace', metavar='format', nargs='?')
    parser.add_argument('-c', '--check', action='store_true')
    return parser



def main(args=None):

    parser = make_parser()
    args = parser.parse_args(args)

    try:
        with args.file as f:
            program = Program.load(f)
        for error in program.check():
            raise error
    except ProgramError as e:
        parser.error("{} (on line {})".format(e.message, e.line_no))

    if args.check:
        parser.exit(message=str(program))

    pu = ProcessingUnit()
    pu.registers.update(args.input)
    # TODO: Implement trace.
    pu.run_program(program)

    # TODO: Implement output.


