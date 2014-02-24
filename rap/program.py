import re
import collections



class ProgramError(Exception):

    def __init__(self, message, line_no=None):
        super().__init__(message, line_no)
        self.message = message
        self.line_no = line_no



class Instruction:

    """Base for all instructions."""

    def __init__(self, step=None, line_no=None):
        self.step = step if step is None else self.make_step(step, 'step')
        self.line_no = line_no

    def run(self, registers):
        raise NotImplementedError

    def check(self, program):
        return
        yield

    @classmethod
    def make_step(cls, value, argument):
        try:
            return int(value)
        except Exception:
            raise ValueError("{} must be an integer".format(argument))

    @classmethod
    def make_register(cls, value, argument):
        if not re.match("^[a-zA-Z0-9]+$", value):
            raise ValueError("{} must be alphanumeric".format(argument))
        return value



class Deb(Instruction):

    """Decrement-or-Branch instruction."""

    def __init__(self, register, go_to_step, branch_to_step,
                 step=None, line_no=None):
        super().__init__(step, line_no)
        self.register = self.make_register(register, 'register')
        self.go_to_step = self.make_step(go_to_step, 'go_to_step')
        self.branch_to_step = self.make_step(branch_to_step, 'branch_to_step')

    def run(self, registers):
        if registers[self.register] == 0:
            return self.branch_to_step
        registers[self.register] -= 1
        return self.go_to_step

    def check(self, program):
        if self.go_to_step not in program:
            yield ProgramError("invalid go_to_step {}".format(self.go_to_step),
                               self.line_no)
        if self.branch_to_step not in program:
            yield ProgramError(
                "invalid branch_to_step {}".format(self.branch_to_step),
                self.line_no)

    def __str__(self):
        return "{:<7} deb     {} {} {}".format(
            self.step, self.register, self.go_to_step, self.branch_to_step)



class Inc(Instruction):

    """Increment instruction."""

    def __init__(self, register, go_to_step, step=None, line_no=None):
        super().__init__(step, line_no)
        self.register = self.make_register(register, 'register')
        self.go_to_step = self.make_step(go_to_step, 'go_to_step')

    def run(self, registers):
        registers[self.register] += 1
        return self.go_to_step

    def check(self, program):
        if self.go_to_step not in program:
            yield ProgramError("invalid go_to_step {}".format(self.go_to_step),
                               self.line_no)

    def __str__(self):
        return "{:<7} inc     {} {}".format(
            self.step, self.register, self.go_to_step)



class End(Instruction):

    """End instruction."""

    def run(self, registers):
        return None

    def __str__(self):
        return "{:<7} end".format(self.step)



class Program(collections.OrderedDict):


    instructions = {
        'deb': Deb,
        'inc': Inc,
        'end': End,
    }


    def __init__(self):
        super().__init__()
        self.start = None


    def __str__(self):
        return '\n'.join(str(i) for i in self.values()) + '\n'


    @classmethod
    def load_line(cls, line, line_no=None):
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
            instruction = instruction(*parts[1:], step=step, line_no=line_no)
        except TypeError:
            raise ProgramError("wrong number of arguments", line_no)
        except ValueError as e:
            raise ProgramError(e, line_no)

        return instruction


    @classmethod
    def load(cls, lines):
        program = cls()
        expected_step = 0

        for line_no, line in enumerate(lines, 1):
            line = line.partition('#')[0].strip()
            if not line:
                continue

            expected_step += 1

            instruction = cls.load_line(line, line_no)

            if instruction.step is not None:
                if instruction.step < expected_step:
                    raise ProgramError("expected step >= {} (got {})"
                        .format(expected_step, instruction.step), line_no)
                expected_step = instruction.step
            else:
                instruction.step = expected_step

            program[expected_step] = instruction

            if program.start is None:
                program.start = expected_step

        return program


    def check(self):
        for instruction in self.values():
            for error in instruction.check(self):
                yield error


