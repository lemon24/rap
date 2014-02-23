"""
Register Assembly Programming

Intuition Pumps and Other Tools for Thinking by Daniel C. Dennett
IV. An Interlude About Computers
24. The Seven Secrets of Computer Power Revealed)

http://sites.tufts.edu/rodrego/


"""
__version__ = '0.1dev'

import collections
import re
import string
import shlex



class Instruction:

    """Base for all instructions."""

    def __init__(self):
        self.command = None

    def run(self, registers):
        raise NotImplementedError

    @classmethod
    def make_step(cls, value, argument):
        try:
            return int(value)
        except Exception:
            raise ValueError("{} must be an integer".format(argument))

    @classmethod
    def make_register(cls, value, argument):
        if not re.match("^[a-z0-9]+$", value):
            raise ValueError("{} must be alphanumeric".format(argument))
        return value



class Deb(Instruction):

    """Decrement-or-Branch instruction."""

    def __init__(self, register, go_to_step, branch_to_step):
        super().__init__()
        self.register = self.make_register(register, 'register')
        self.go_to_step = self.make_step(go_to_step, 'go_to_step')
        self.branch_to_step = self.make_step(branch_to_step, 'branch_to_step')

    def run(self, registers):
        if registers[self.register] == 0:
            return self.branch_to_step
        registers[self.register] -= 1
        return self.go_to_step

    def __str__(self):
        return "deb     {:<3} {:<3} {:<3}".format(
            self.register, self.go_to_step, self.branch_to_step)



class Inc(Instruction):

    """Increment instruction."""

    def __init__(self, register, go_to_step):
        super().__init__()
        self.register = self.make_register(register, 'register')
        self.go_to_step = self.make_step(go_to_step, 'go_to_step')

    def run(self, registers):
        registers[self.register] += 1
        return self.go_to_step

    def __str__(self):
        return "inc     {:<3} {:<3}".format(self.register, self.go_to_step)



class End(Instruction):

    """End instruction."""

    def run(self, registers):
        return None

    def __str__(self):
        return "end"



class Registers(collections.Counter):

    def __str__(self):
        pairs = ("{}: {}".format(r, v) for r, v in sorted(self.items()))
        return ', '.join(pairs)



class ProcessingUnit:

    registers_cls = Registers

    def __init__(self):
        self.registers = self.registers_cls()

    def run_program(self, program):
        next_step = program.start
        while next_step is not None:
            instruction = program[next_step]
            if instruction.command:
                instruction.command.before(self)
            next_step = instruction.run(self.registers)
            if instruction.command:
                instruction.command.after(self)



class Command:

    """Base for all commands."""

    def before(self, pu):
        pass

    def after(self, pu):
        pass



class PrintCommand(Command):


    class command_template(string.Template):

        idpattern = "[_a-z0-9]+"


    def __init__(self, args):
        self.templates = [self.command_template(a) for a in args]

    def before(self, pu):
        rs = pu.registers
        print(' '.join(t.safe_substitute(rs) for t in self.templates))



class ProgramError(Exception):

    def __init__(self, message, line_no=None):
        super().__init__(message, line_no)
        self.message = message
        self.line_no = line_no



class Program(collections.OrderedDict):


    instructions = {
        'deb': Deb,
        'inc': Inc,
        'end': End,
    }

    commands = {
        'print': PrintCommand,
    }


    def __init__(self):
        super().__init__()
        self.start = None


    @classmethod
    def load_line(cls, line, line_no=None):
        line, sep, command = line.partition('!')
        parts = line.split()
        try:
            step = int(parts[0])
            parts = parts[1:]
        except ValueError:
            step = None

        if step is not None and not parts:
            raise ProgramError("expected instruction", line_no)

        instruction = cls.instructions.get(parts[0])
        if not instruction:
            raise ProgramError("invalid instruction", line_no)
        try:
            instruction = instruction(*parts[1:])
        except TypeError:
            raise ProgramError("wrong number of arguments", line_no)
        except ValueError as e:
            raise ProgramError(e, line_no)

        command = shlex.split(command, comments=True)
        if command:
            command_cls = cls.commands.get(command[0])
            if not command_cls:
                raise ProgramError("unknown command: {!r}".format(command[0]),
                                   line_no)
            instruction.command = command_cls(command[1:])

        return step, instruction


    @classmethod
    def load(cls, lines):
        program = cls()
        expected_step = 0

        for line_no, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            expected_step += 1

            step, instruction = cls.load_line(line, line_no)
            if step is not None:
                if step < expected_step:
                    raise ProgramError("expected step >= {} (got {})"
                        .format(expected_step, step), line_no)
                expected_step = step

            if program.start is None:
                program.start = expected_step

            program[expected_step] = instruction

        return program


    def __str__(self):
        lines = ("{:<7} {}".format(n, s) for n, s in self.items())
        return '\n'.join(lines)




if __name__ == "__main__":

    import sys
    try:
        with open(sys.argv[1]) as f:
            program = Program.load(f)
    except ProgramError as e:
        sys.exit("syntax error: {} (on line {})".format(e.message, e.line_no))

    print(program)

    pu = ProcessingUnit()
    reg = pu.registers
    reg['1'] = 5
    reg['2'] = 2


    pu.run_program(program)
    print(reg)

