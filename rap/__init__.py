
__version__ = '0.1dev'

import argparse
import string
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



class Formatter(string.Formatter):

    """Slightly modified string.Formatter.

    The differences are:
    - field names are considered strings (i.e. only kwargs are used)
    - field names / attributes / items that are not found are silently
      ignored and their corresponding replacement fields are preserved
    - invalid replacement fields are are also silently preserved

    """

    def get_field(self, field_name, args, kwargs):

        first, rest = string._string.formatter_field_name_split(field_name)
        obj = self.get_value(str(first), args, kwargs)

        for is_attr, i in rest:
            if is_attr:
                obj = getattr(obj, i)
            else:
                obj = obj[str(i)]

        return obj, first


    def _vformat(self, format_string, args, kwargs, used_args, recursion_depth):
        if recursion_depth < 0:
            raise ValueError('Max string recursion exceeded')
        result = []
        for literal_text, field_name, format_spec, conversion in \
                self.parse(format_string):
            original_format_spec = format_spec

            if literal_text:
                result.append(literal_text)

            if field_name is not None:
                used_args_copy = used_args.copy()
                try:
                    obj, arg_used = self.get_field(field_name, args, kwargs)
                    used_args_copy.add(arg_used)

                    obj = self.convert_field(obj, conversion)

                    format_spec = self._vformat(format_spec, args, kwargs,
                                                used_args_copy, recursion_depth-1)

                    formatted = self.format_field(obj, format_spec)

                    result.append(formatted)
                    used_args.update(used_args_copy)

                except (AttributeError, KeyError, ValueError):
                    result.append("{" + field_name)
                    if conversion:
                        result.append("!" + conversion)
                    if original_format_spec:
                        result.append(":" + original_format_spec)
                    result.append("}")

        return ''.join(result)



def make_parser():
    # TODO: Add help and description strings.
    parser = argparse.ArgumentParser('rap')
    parser.add_argument('file', type=argparse.FileType('r'))
    parser.add_argument('-i', '--input', metavar='input', type=parse_input)
    parser.add_argument('-o', '--output', metavar='format', nargs='?', const=True)
    parser.add_argument('-t', '--trace', metavar='format', nargs='?', const=True)
    parser.add_argument('-s', '--start', metavar='step', type=int)
    parser.add_argument('-c', '--check', action='store_true')
    return parser



def make_printer(what):
    if what is None:
        return None
    if what is True:
        return lambda pu: print(pu.registers)

    formatter = Formatter()
    def printer(pu):
        names = dict(pu.registers)
        print(formatter.vformat(what, (), names))

    return printer



def main(args=None):

    parser = make_parser()
    args = parser.parse_args(args)

    # TODO: validate args.output and args.trace
    # TODO: decode character escapes for args.output and args.trace

    try:
        with args.file as f:
            program = Program.load(f)
        for error in program.check():
            raise error
    except ProgramError as e:
        parser.error("{} (on line {})".format(e.message, e.line_no))

    if args.check:
        parser.exit(message=str(program))

    if args.start is None:
        start = program.start
    elif args.start in program:
        start = args.start
    else:
        parser.error("step {} not in program".format(args.start))

    trace = make_printer(args.trace)
    if trace and args.output is True:
        output = trace
    else:
        output = make_printer(args.output)

    pu = ProcessingUnit()
    pu.registers.update(args.input)
    pu.run_program(program, start, trace)

    if output:
        output(pu)


