import re
import collections



def natural_sort_key(string, split_by=re.compile("([0-9]+)")):
    return tuple(int(s) if s.isdigit() else s for s in split_by.split(string))



class Registers(collections.Counter):

    def __str__(self):
        pairs = sorted(self.items(), key=lambda p: natural_sort_key(p[0]))
        return ', '.join("{}: {}".format(r, v) for r, v in pairs)



class ProcessingUnit:

    registers_cls = Registers

    def __init__(self):
        self.registers = self.registers_cls()

    def run_program(self, program):
        next_step = program.start
        while next_step is not None:
            instruction = program[next_step]
            next_step = instruction.run(self.registers)


