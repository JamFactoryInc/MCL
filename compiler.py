from __future__ import print_function
from types import CodeType
import byte_code, dis
from typing import List, Dict, Optional, Tuple

WRITE_DIR = r"C:\Users\jam\AppData\Roaming\.minecraft\saves\MCL Testing\datapacks\mcl\data\mcl\functions"
WRITE_DATAPACK = False

"""
* Optimizations:
when declaring a list literal, an unnecessary BUILD_LIST and LIST_EXTEND are used
replicate:
```
[1,2,3]
```
* saves 2 commands per instance

when a name is stored then loaded, there is an unnecessary pop and push
replicate:
```
i = 1
i + 1
```
* saves 2 commands per instance

when storing co_names, there is a check whether to append or set, resulting in 1 redundant line. This can be skipped via making co_names a dict
replicate:
i = 1
i = 2
* saves 1 command per instance
"""

"""
! bugs
if FOR_ITER is the instruction after a jump e.g. a for loop or if statement,
it could falsely start a for loop, as only is_jump_target=True is checked when making a for loop

if something is done inside a function call, it injects another instruction (or more) between the function and the load_name
another method of determining the name of the called function is required
"""

GLOBALS = ['print', 'select']
GLOBAL_METHODS = ['str', 'len']
queued_ends = []

def numeric_to_value(number):
    sign = 1 if number > 0 else -1
    num = abs(number)
    dec = len(str(num)) - len(str(int(num))) - 1
    return f"{{dec:{dec if type(number) == float else 0},num:{[int(d) for d in str(num) if d != '.']},pol:{sign},base:10}}"

def list_to_value(list):
    ret = '['
    for v in list:
        if type(v) == int or type(v) == float:
            ret += (numeric_to_value(v))
        elif type(v) == str:
            if len(v) > 1:
                ret += list_to_value(v)
            else:
                ret += '"' + v + '"'
        elif type(v) == list or type(v) == tuple:
            ret += (list_to_value(v))
        ret += ','
    return ret[:-1] + ']'

class Function:
    index = 0
    active = None
    functions = []
    def __init__(self, name, lines=[], parent_fn = None, end_lines = []):
        self.lines = lines
        self.name = name
        self.parent = parent_fn
        self.end_lines = end_lines
        Function.index += 1
        Function.functions.append(self)

    def add_lines(self, lines):
        self.lines = self.lines + lines

    def end(self):
        self.add_lines(self.end_lines)

    def __repr__(self):
        s = '# ' + self.name + '\n'
        for l in self.lines:
            s += l + '\n'
        return s

load_fn = Function("load")

load_fn.add_lines(["data modify storage mcl:main stack set value [[]]",
                   "data modify storage mcl:main co_names set value []",
                   "data remove storage mcl:main temp",
                   'tellraw @a {"text":"Reloaded and ready to rock","italic":true,"color":"green"}',
                   "kill @e[tag=read_head, type=minecraft:marker]",
                   "execute in mcl:mcl/void run summon minecraft:marker 0 0 0 {Tags:['read_head']}",
                   "# set up array to help turn numbers into strings",
                   'execute in mcl:mcl/void unless block 0 0 0 minecraft:dropper run setblock 0 0 0 minecraft:dropper{Items:[{Count:1b,Slot:0b,id:"minecraft:paper",tag:{num_to_str:"0"}}]}',
                   'execute in mcl:mcl/void unless block 1 0 0 minecraft:dropper run setblock 1 0 0 minecraft:dropper{Items:[{Count:1b,Slot:0b,id:"minecraft:paper",tag:{num_to_str:"1"}}]}',
                   'execute in mcl:mcl/void unless block 2 0 0 minecraft:dropper run setblock 2 0 0 minecraft:dropper{Items:[{Count:1b,Slot:0b,id:"minecraft:paper",tag:{num_to_str:"2"}}]}',
                   'execute in mcl:mcl/void unless block 3 0 0 minecraft:dropper run setblock 3 0 0 minecraft:dropper{Items:[{Count:1b,Slot:0b,id:"minecraft:paper",tag:{num_to_str:"3"}}]}',
                   'execute in mcl:mcl/void unless block 4 0 0 minecraft:dropper run setblock 4 0 0 minecraft:dropper{Items:[{Count:1b,Slot:0b,id:"minecraft:paper",tag:{num_to_str:"4"}}]}',
                   'execute in mcl:mcl/void unless block 5 0 0 minecraft:dropper run setblock 5 0 0 minecraft:dropper{Items:[{Count:1b,Slot:0b,id:"minecraft:paper",tag:{num_to_str:"5"}}]}',
                   'execute in mcl:mcl/void unless block 6 0 0 minecraft:dropper run setblock 6 0 0 minecraft:dropper{Items:[{Count:1b,Slot:0b,id:"minecraft:paper",tag:{num_to_str:"6"}}]}',
                   'execute in mcl:mcl/void unless block 7 0 0 minecraft:dropper run setblock 7 0 0 minecraft:dropper{Items:[{Count:1b,Slot:0b,id:"minecraft:paper",tag:{num_to_str:"7"}}]}',
                   'execute in mcl:mcl/void unless block 8 0 0 minecraft:dropper run setblock 8 0 0 minecraft:dropper{Items:[{Count:1b,Slot:0b,id:"minecraft:paper",tag:{num_to_str:"8"}}]}',
                   'execute in mcl:mcl/void unless block 9 0 0 minecraft:dropper run setblock 9 0 0 minecraft:dropper{Items:[{Count:1b,Slot:0b,id:"minecraft:paper",tag:{num_to_str:"9"}}]}'])

Function.active = load_fn

constants = []
prev_calls = []

invoker = Function("util\\invoker")
method_invoker = Function("util\\method_invoker")
method_invoker.add_lines(
    [f'execute if data storage mcl:main temp.instance{{type:"list"}} if data storage mcl:main temp.callable{{value:"append", type:"callable"}} run function mcl:methods/list_append',
     f'execute if data storage mcl:main temp.instance{{type:"list"}} if data storage mcl:main temp.callable{{value:"len", type:"callable"}} run function mcl:methods/list_len'])

def start_method(name):
    method_type, method_name = name.split('_')
    method_invoker.add_lines(
        [f'execute if data storage mcl:main temp.instance{{type:"{method_type}"}} if data storage mcl:main temp.callable{{value:"{method_name}"}} run function mcl:methods/{name}'])
    method = Function("methods\\" + name)
    Function.active = method

list_append = Function("methods\\list_append")
list_append.add_lines(["data modify storage mcl:main temp.instance.value append from storage mcl:main temp.args[0].value",
                       "data modify storage mcl:main stack[0] prepend from storage mcl:main temp.instance"])

list_len = Function("methods\\list_len")
list_len.add_lines(
    ["data modify storage mcl:main stack[0] prepend value {value:['n','o']}"])

def not_implemented(feature : str, line: int):
    print(
        f"\033[93mWarning beginning line {line}: {feature} not yet implemented\033[0m")

def warning(warn : str, line: int):
    print(
        f"\033[93mWarning beginning line {line}: {warn}\033[0m")

def add_lines(lines : List[str]):
    Function.active.add_lines(lines)

def remove_line():
    Function.active.lines.pop()

def add_lines_init(lines : List[str]):
    load_fn.add_lines(lines)

def queue_end_on_instr(line):
    queued_ends.append(line)

def end():
    Function.active.end()
    Function.active = Function.active.parent

def start_fn(fn_name, num_args):
    new_fn = Function("user_functions\\" + fn_name, parent_fn=Function.active)
    Function.active = new_fn

def add_fn(fn_name):
    global invoker
    invoker.add_lines([f'execute if data storage mcl:main temp.callable{{value:"{fn_name}", type:"callable"}} run function mcl:user_functions/{fn_name}'])

def start_while(condition : str):
    """Executes lines as long as the execute if condition returns true

    Args:
        lines (List[str]): lines to loop over
        condition (str): condition to loop until false
    """,
    index = Function.index
    Function.active.add_lines([condition + f" function mcl:util/fn{index}"])
    new_fn = Function(f"util\\fn{index}", parent_fn=Function.active, end_lines=[
                      "# Recursively call function to emulate loop",
                      condition + f" function mcl:util/fn{index}",])
    Function.active = new_fn

def start_if(condition:str):
    index = Function.index
    Function.active.add_lines([condition + f" function mcl:util/fn{index}"])
    new_fn = Function(f"util\\fn{index}", parent_fn=Function.active)
    Function.active = new_fn

def compile(filename:str, code_obj = None):
    global prev_calls
    bytecode = iter(byte_code.get_bytecode(filename)
                    ) if str and not code_obj else iter(dis.Bytecode(code_obj))

    current_line = 0
    current_instr = -1
    for inst in bytecode:
        current_line = inst.starts_line if inst.starts_line else current_line
        current_instr += 1
        print(current_instr, inst, current_line)
        while current_instr in queued_ends:
            print('ended')
            end()
            queued_ends.remove(current_instr)
        match inst.opcode:
            case 1:
                # POP TOP
                # 12345 -> 2345
                add_lines(["# POP TOP",
                           "data remove storage mcl:main stack[0][0]"])
            case 2:
                # ROT TWO
                # 12345 -> 21345
                add_lines(
                    ["data modify storage mcl:main stack[0] insert 2 from storage mcl:main stack[0][0]",
                     "data remove storage mcl:main stack[0][0]"])
            case 3:
                # ROT THREE
                # 12345 -> 23145
                add_lines(
                    ["data modify storage mcl:main stack[0] insert 3 from storage mcl:main stack[0][0]",
                     "data remove storage mcl:main stack[0][0]"])
            case 4:
                # DUP TOP
                # 12345 -> 112345
                add_lines(
                    ["data modify storage mcl:main stack[0] prepend from storage mcl:main stack[0][0]"])
            case 5:
                # DUP TOP TWO
                # 12345 -> 1212345
                add_lines(
                    ["data modify storage mcl:main stack[0] prepend from storage mcl:main stack[0][1]",
                     "data modify storage mcl:main stack[0] prepend from storage mcl:main stack[0][1]"])
            case 6:
                # ROT FOUR
                # 12345 -> 23415
                add_lines(
                    ["data modify storage mcl:main stack[0] insert 4 from storage mcl:main stack[0][0]",
                     "data remove storage mcl:main stack[0][0]"])

            case 10:
                # UNARY POSITIVE
                # TOS = +TOS
                warning("Unary positive not implemented. It's generally not useful and thus I didn't deem it necessary. If you disagree, then please contact the developer", current_line)
            case 11:
                # UNARY NEGATIVE
                # TOS = -TOS
                # ! this could be made more efficient
                add_lines(
                    ["data modify storage arr_math:in var1 set from storage mcl:main stack[0][0].value",
                     "data modify storage arr_math:in var2 set value {dec:0, num:[1,],pol:-1,base:10}",
                     "function arr_math:call/multiply",
                     "data modify storage mcl:main stack[0][0].value.pol set from storage arr_math:main out"])
            case 12:
                # UNARY NOT
                # TOS = not TOS
                print(12)

            case 15:
                # UNARY INVERT
                # TOS = ~TOS
                not_implemented("binary")
            case 16:
                # BINARY MATRIX MULTIPLY
                # TOS = TOS1 @ TOS
                # 1 2 3 4 5 -> 2@1 2 3 4 5
                not_implemented("matrix multiplication")
            case 17:
                # INPLACE MATRIX MULTIPLY
                # TOS = TOS1 @ TOS
                # 1 2 3 4 5 -> 2@1 2 3 4 5
                not_implemented("matrix multiplication")

            case 19:
                # BINARY POWER
                # TOS = TOS1 ** TOS
                # 1 2 3 4 5 -> 2**1 2 3 4 5
                warning(
                    "** is only compatible with integer exponents; Any decimals will be truncated. Use Math.root instead of fractional exponents")

                # copy power to scoreboard
                add_lines(["data modify storage arr_math:in var1 set from storage mcl:main stack[0][0].value",
                           "function arr_math:call/scoreboard/export",
                           "data modify storage arr_math:in var2 set from storage mcl:main stack[0][1].value"])

                # if power is positive
                start_if("execute if score out= arr_math.main matches 1.. run")
                start_while(
                    "execute unless score out= arr_math.main matches 0 run")
                add_lines(
                    ["data modify storage arr_math:in var2 set from storage arr_math:main out",
                     "function arr_math:call/multiply"])
                end()
                add_lines(
                    ["data modify storage mcl:main stack[0][0].value set from storage arr_math:main out"])
                end()

                # if power is positive
                start_if("execute if score out= arr_math.main matches 1.. run")
                start_while(
                    "execute unless score out= arr_math.main matches 0 run")
                add_lines(
                    ["data modify storage arr_math:in var2 set from storage arr_math:main out",
                     "function arr_math:call/multiply"])
                end()
                add_lines(
                    ["data modify storage mcl:main stack[0][0].value set from storage arr_math:main out"])
                end()

                # if power is zero
                start_if("execute if score out= arr_math.main matches 0 run")
                add_lines(
                    ["data modify storage mcl:main stack[0][0].value set value {dec:0, num:[1],pol:1,base:10}"])
                end()
            case 20:
                # BINARY MULTIPLY
                # TOS = TOS1 * TOS
                # 1 2 3 4 5 -> 2*1 3 4 5
                add_lines(
                    ["# BINARY MULTIPLY",
                     "data modify storage arr_math:in var1 set from storage mcl:main stack[0][0].value",
                     "data modify storage arr_math:in var2 set from storage mcl:main stack[0][1].value",
                     "function arr_math:call/multiply",
                     "data remove storage mcl:main stack[0][0]",
                     "data modify storage mcl:main stack[0][0].value set from storage arr_math:main out"])

            case 22:
                # BINARY MODULO
                # TOS = TOS1 % TOS
                # 1 2 3 4 5 -> 2%1 3 4 5
                # FIXME old standard
                add_lines_init(["scoreboard objectives add mcl0 dummy",
                                "scoreboard objectives add mcl1 dummy"])
                add_lines([
                    "# BINARY MODULO",
                    "data modify storage arr_math:in var1 set from storage mcl:main stack[0][1].value",
                    "function arr_math:call/scoreboard/export",
                    "scoreboard players operation #mcl mcl0 = out= arr_math.main",
                    "data modify storage arr_math:in var1 set from storage mcl:main stack[0][0].value",
                    "function arr_math:call/scoreboard/export",
                    "scoreboard players operation #mcl mcl0 %= out= arr_math.main",
                    "data remove storage mcl:main stack[0][0]",
                    "scoreboard players operation in= arr_math.main = #mcl mcl0",
                    "function arr_math:call/scoreboard/import",
                    "data modify storage mcl:main stack[0][0].value set from storage arr_math:main out"])
            case 23:
                # BINARY ADD
                # TOS = TOS1 + TOS
                # 1 2 3 4 5 -> 2+1 3 4 5
                start_if(
                    "execute if data storage mcl:main stack[0][0].value.num run")
                add_lines(
                    ["data modify storage arr_math:in var1 set from storage mcl:main stack[0][0].value",
                     "data modify storage arr_math:in var2 set from storage mcl:main stack[0][1].value",
                     "function arr_math:call/add",
                     "data remove storage mcl:main stack[0][0]",
                     "data modify storage mcl:main stack[0][0].value set from storage arr_math:main out"])
                end()
                start_if(
                    "execute unless data storage mcl:main stack[0][1].value.num run")
                add_lines(
                    ["data modify storage mcl:main stack[0][1].value append from storage mcl:main stack[0][0].value[]",
                     "data remove storage mcl:main stack[0][0]"])
                end()
            case 24:
                # BINARY SUBTRACT
                # TOS = TOS1 - TOS
                # 1 2 3 4 5 -> 2-1 3 4 5
                add_lines(
                    ["data modify storage arr_math:in var1 set from storage mcl:main stack[0][1].value",
                     "data modify storage arr_math:in var2 set from storage mcl:main stack[0][0].value",
                     "function arr_math:call/subtract",
                     "data remove storage mcl:main stack[0][0]",
                     "data modify storage mcl:main stack[0][0].value set from storage arr_math:main out"])
            case 25:
                # BINARY SUBSCR
                # TOS = TOS1[TOS]
                # 1 2 3 4 5 -> 2[1] 3 4 5
                # variable subscr algorithm provided by u/TheMrZZ0
                add_lines_init(["scoreboard objectives add mcl0 dummy",
                                "scoreboard objectives add mcl1 dummy"])

                # if index is positive
                add_lines(
                    ["data modify storage mcl:main temp set from storage mcl:main stack[0][1]",
                     "data modify storage mcl:main temp1 set from storage mcl:main stack[0][0].value",
                     "execute store result score #mcl mcl0 run data get storage mcl:main temp1",
                     "scoreboard players set #mcl mcl1 0"])
                start_if("execute if score #mcl mcl0 matches 0.. run")
                start_while("execute if data storage mcl:main temp[0] run")
                add_lines(["scoreboard players remove #mcl mcl0 1",
                           "data remove storage mcl:main temp[0]"])
                end()
                add_lines(
                    ["data remove storage mcl:main stack[0][0]",
                     "data modify storage mcl:main stack[0][0] set from storage mcl:main temp[0]"])
                end()

                # if index is negative
                start_if("execute if score #mcl mcl0 matches ..-1 run")
                start_while("execute unless score #mcl mcl0 matches -1 run")
                add_lines(["scoreboard players add #mcl mcl0 1",
                           "data remove storage mcl:main temp[-1]"])
                end()
                add_lines(
                    ["data remove storage mcl:main stack[0][0]",
                     "data modify storage mcl:main stack[0][0] set from storage mcl:main temp[-1]"])
                end()

            case 26:
                # BINARY FLOOR DIVIDE
                # TOS = TOS1 // TOS
                # 1 2 3 4 5 -> 2//1 3 4 5
                add_lines_init(["scoreboard objectives add mcl0 dummy",
                                "scoreboard objectives add mcl1 dummy"])
                add_lines(
                    "data modify storage arr_math:in var1 set from storage mcl:main stack[0][0].value",
                    "function arr_math:call/scoreboard/export",
                    "scoreboard players operation #mcl mcl0 = out= arr_math.main",
                    "data modify storage arr_math:in var1 set from storage mcl:main stack[0][1].value",
                    "function arr_math:call/scoreboard/export",
                    "scoreboard players operation out= arr_math.main /= #mcl mcl0",
                    "scoreboard players operation in= arr_math.main = out= arr_math.main",
                    "function arr_math:call/scoreboard/import",
                    "data remove storage mcl:main stack[0][0]",
                    "data modify storage mcl:main stack[0][0].value set from storage arr_math:main out")
            case 27:
                # BINARY DIVIDE
                # TOS = TOS1 / TOS
                # 1 2 3 4 5 -> 2/1 3 4 5
                add_lines(
                    ["data modify storage arr_math:in var1 set from storage mcl:main stack[0][1].value",
                     "data modify storage arr_math:in var2 set from storage mcl:main stack[0][0].value",
                     "function arr_math:call/divide",
                     "data remove storage mcl:main stack[0][0]",
                     "data modify storage mcl:main stack[0][0].value set from storage arr_math:main out"])
            case 28:
                # INPLACE FLOOR DIVIDE
                # TOS = TOS1 // TOS
                # 1 2 3 4 5 -> 2//1 3 4 5
                add_lines_init(["scoreboard objectives add mcl0 dummy",
                                "scoreboard objectives add mcl1 dummy"])
                add_lines(
                    "data modify storage arr_math:in var1 set from storage mcl:main stack[0][0].value",
                    "function arr_math:call/scoreboard/export",
                    "scoreboard players operation #mcl mcl0 = out= arr_math.main",
                    "data modify storage arr_math:in var1 set from storage mcl:main stack[0][1].value",
                    "function arr_math:call/scoreboard/export",
                    "scoreboard players operation out= arr_math.main /= #mcl mcl0",
                    "scoreboard players operation in= arr_math.main = out= arr_math.main",
                    "function arr_math:call/scoreboard/import",
                    "data remove storage mcl:main stack[0][0]",
                    "data modify storage mcl:main stack[0][0].value set from storage arr_math:main out")
            case 29:
                # INPLACE DIVIDE
                # TOS = TOS1 / TOS
                # 1 2 3 4 5 -> 2/1 3 4 5
                add_lines(
                    ["data modify storage arr_math:in var1 set from storage mcl:main stack[0][1].value",
                     "data modify storage arr_math:in var2 set from storage mcl:main stack[0][0].value",
                     "function arr_math:call/divide",
                     "data modify storage mcl:main stack[0][0].value set from storage arr_math:main out"])
            case 30:
                # GET LEN
                # 1 2 3 4 5 -> len(1) 1 2 3 4 5
                add_lines_init(["scoreboard objectives add mcl0 dummy",
                                "scoreboard objectives add mcl1 dummy"])

                add_lines(
                    ["data modify storage mcl:main temp set from storage mcl:main stack[0][0]",
                     "scoreboard players set #mcl mcl0 0"])
                start_while("execute if data storage mcl:main temp[0] run")
                add_lines(["scoreboard players add #mcl 1",
                            "data remove storage mcl:main temp[0]"])
                end()
                add_lines(
                    ["data modify storage mcl:main stack[0] prepend value [0]",
                     "execute store result storage mcl:main stack[0][0].value int 1 run scoreboard players get #mcl mcl1"])
            case 31:
                # MATCH MAPPING
                # ! No idea what this is
                print(31)
            case 32:
                # MATCH SEQUENCE
                # ! No idea what this is
                print(32)
            case 33:
                # MATCH KEYS
                # ! No idea what this is
                print(33)
            case 34:
                # COPY DICT WITHOUT KEYS
                # ! No idea what this is
                print(34)

            case 49:
                # WITH EXCEPT START
                not_implemented('error handling', current_line)
            case 50:
                # GET AITER
                not_implemented('async behavior', current_line)
            case 51:
                # GET ANEXT
                not_implemented('async behavior', current_line)
            case 52:
                # BEFORE ASYNC WITH
                not_implemented('async behavior', current_line)

            case 54:
                # END ASYNC FOR
                not_implemented('async behavior', current_line)
            case 55:
                # INPLACE ADD
                # TOS = TOS1 + TOS
                start_if("execute if data storage mcl:main stack[0][0].value.num run")
                add_lines(
                    ["data modify storage arr_math:in var1 set from storage mcl:main stack[0][0].value",
                     "data modify storage arr_math:in var2 set from storage mcl:main stack[0][1].value",
                     "function arr_math:call/add",
                     "data remove storage mcl:main stack[0][0]",
                     "data modify storage mcl:main stack[0][0].value set from storage arr_math:main out"])
                end()
                start_if(
                    "execute unless data storage mcl:main stack[0][1].value.num run")
                add_lines(
                    ["data modify storage mcl:main stack[0][1].value append from storage mcl:main stack[0][0].value[]",
                     "data remove storage mcl:main stack[0][0]"])
                end()
            case 56:
                # INPLACE SUBTRACT
                # TOS = TOS1 - TOS
                add_lines(
                    ["data modify storage arr_math:in var1 set from storage mcl:main stack[0][1].value",
                     "data modify storage arr_math:in var2 set from storage mcl:main stack[0][0].value",
                     "function arr_math:call/subtract",
                     "data remove storage mcl:main stack[0][0]",
                     "data modify storage mcl:main stack[0][0].value set from storage arr_math:main out"])
            case 57:
                # INPLACE MULTIPLY
                # TOS = TOS1 * TOS
                add_lines(
                    ["data modify storage arr_math:in var1 set from storage mcl:main stack[0][1].value",
                     "data modify storage arr_math:in var2 set from storage mcl:main stack[0][0].value",
                     "function arr_math:call/multiply",
                     "data remove storage mcl:main stack[0][0]",
                     "data modify storage mcl:main stack[0][0].value set from storage arr_math:main out"])

            case 59:
                # INPLACE MODULO
                # TOS = TOS1 % TOS
                print(59)
            case 60:
                # STORE SUBSCR
                # TOS1[TOS] = TOS2
                add_lines_init(["function arr_math:setup"])

                add_lines(["# STORE SUBSCR",
                           "# TOS1 is subscriptable, TOS is index, TOS2 is value",
                           "data modify storage mcl:main temp set value []",
                           "# Store TOS as an int in a scoreboard objective",
                           "data modify storage arr_math:in var1 set from storage mcl:main stack[0][0].value",
                           "function arr_math:call/scoreboard/export",
                           "# Call until scoreboard value out= arr_math.main is 0"])

                start_while(
                    "execute unless score out= arr_math.main matches 0 run")

                add_lines(["scoreboard players remove out= arr_math.main 1",
                           "# TOS1 should be a subscriptable. TOS1[0] is popped and appended to temp",
                           "data modify storage mcl:main temp append from storage mcl:main stack[0][1].value[0]",
                           "data remove storage mcl:main stack[0][1].value[0]"])
                end()

                add_lines(["# set now-exposed index of TOS1 to be TOS2",
                           "data modify storage mcl:main stack[0][1].value[0] set from storage mcl:main stack[0][2].value",
                           "# Prepend popped values back to the subscriptable",
                           "data modify storage mcl:main stack[0][1].value prepend from storage mcl:main temp[]",
                           "# Pop TOS and TOS2 from stack",
                           "data remove storage mcl:main stack[0][0]",
                           "data remove storage mcl:main stack[0][1]",
                           "# Store name and remove from stack. This is to overcome the fact that I'm not using pointers",
                           f"data modify storage mcl:main co_names[{prev_calls[-2].arg}] set from storage mcl:main stack[0][0]",
                           "data remove storage mcl:main stack[0][0]"])
            case 61:
                # DELETE SUBSCR
                # del TOS1[TOS]
                add_lines_init(["function arr_math:setup"])

                add_lines(["data modify storage mcl:main temp set value []",
                           "data modify storage arr_math:in var1 set from storage mcl:main stack[0][0].value",
                           "function arr_math:call/scoreboard/export"])

                start_while(
                    "execute unless score out= arr_math.main matches 0 run")

                add_lines(["scoreboard players remove out= arr_math.main 1",
                           "data modify storage mcl:main temp prepend from storage mcl:main stack[0][1].value[0]",
                           "data remove storage mcl:main stack[0][1].value[0]"])
                end()

                add_lines(["data remove storage mcl:main stack[0][1].value[0]",
                           "data modify storage mcl:main stack[0][1].value prepend from storage mcl:main temp[]"])
            case 62:
                # BINARY LSHIFT
                # TOS = TOS1 << TOS
                not_implemented('binary', current_line)
            case 63:
                # BINARY RSHIFT
                # TOS = TOS1 >> TOS
                not_implemented('binary', current_line)
            case 64:
                # BINARY AND
                # TOS = TOS1 & TOS
                not_implemented('binary', current_line)
            case 65:
                # BINARY XOR
                # TOS = TOS1 ^ TOS
                not_implemented('binary', current_line)
            case 66:
                # BINARY OR
                # TOS = TOS1 | TOS
                not_implemented('binary', current_line)
            case 67:
                # INPLACE POWER
                # TOS = TOS1 ** TOS
                warning("** is only compatible with integer exponents; Any decimals will be truncated. Use Math.root instead of fractional exponents")

                # copy power to scoreboard
                add_lines(["data modify storage arr_math:in var1 set from storage mcl:main stack[0][0].value",
                           "function arr_math:call/scoreboard/export",
                           "data modify storage arr_math:in var2 set from storage mcl:main stack[0][1].value"])

                # if power is positive
                start_if("execute if score out= arr_math.main matches 1.. run")
                start_while(
                    "execute unless score out= arr_math.main matches 0 run")
                add_lines(
                    ["data modify storage arr_math:in var2 set from storage arr_math:main out",
                     "function arr_math:call/multiply"])
                end()
                add_lines(
                    ["data remove storage mcl:main stack[0][0]",
                     "data modify storage mcl:main stack[0][0].value set from storage arr_math:main out"])
                end()

                # if power is positive
                start_if("execute if score out= arr_math.main matches 1.. run")
                start_while(
                    "execute unless score out= arr_math.main matches 0 run")
                add_lines(
                    ["data modify storage arr_math:in var2 set from storage arr_math:main out",
                     "function arr_math:call/multiply"])
                end()
                add_lines(
                    ["data modify storage mcl:main stack[0][0].value set from storage arr_math:main out"])
                end()

                # if power is zero
                start_if("execute if score out= arr_math.main matches 0 run")
                add_lines(
                    ["data remove storage mcl:main stack[0][0]",
                     "data modify storage mcl:main stack[0][0].value set value {dec:0, num:[1],pol:1,base:10}"])
                end()

            case 68:
                # GET ITER
                not_implemented('iterators', current_line)
            case 69:
                # GET YIELD FROM ITER
                not_implemented('iterators', current_line)
            case 70:
                # PRINT EXPR
                # 1 2 3 4 5 -> 2 3 4 5
                # > 1
                add_lines(['tellraw @a {"nbt":"stack[0][0].value","storage":"mcl:main"}',
                           "data remove storage mcl:main stack[0][0]"])
            case 71:
                # LOAD BUILD CLASS
                # pushes a class onto the stack[0]. CALL FUNCTION is later used to
                # constuct an instance
                print(71)
            case 72:
                # YIELD FROM
                not_implemented('generators', current_line)
            case 73:
                # GET AWAITABLE
                not_implemented('async behavior', current_line)
            case 74:
                # LOAD ASSERTION ERROR
                not_implemented('assertions', current_line)
            case 75:
                # INPLACE LSHIFT
                # TOS = TOS1 << TOS
                not_implemented('binary', current_line)
            case 76:
                # INPLACE RSHIFT
                # TOS = TOS1 >> TOS
                not_implemented('binary', current_line)
            case 77:
                # INPLACE AND
                # TOS = TOS1 & TOS
                not_implemented('binary', current_line)
            case 78:
                # INPLACE XOR
                # TOS = TOS1 ^ TOS
                not_implemented('binary', current_line)
            case 79:
                # INPLACE OR
                # TOS = TOS1 | TOS
                not_implemented('binary', current_line)

            case 82:
                # LIST TO TUPLE
                # 1 2 3 4 5 -> tuple(1) 2 3 4 5
                warning("tuples and lists are functionally identical in MCL")
            case 83:
                # RETURN VALUE
                # Returns TOS to the caller of the function

                # push TOS of top stack to second stack
                # delete top stack
                add_lines(["data modify storage mcl:main stack[1] prepend from storage mcl:main stack[0][0]",
                          "data remove storage mcl:main stack[0]"])
            case 84:
                # IMPORT STAR
                # This is meta and shouldn't be compiled
                pass
            case 85:
                # SETUP ANNOTATIONS
                not_implemented('annotations', current_line)
            case 86:
                # YIELD VALUE
                not_implemented('annotations', current_line)
            case 87:
                # POP BLOCK
                # Removes one block from the block stack[0]
                print(87)

            case 89:
                # POP EXCEPT
                not_implemented('error handling', current_line)
                print(89)
            case 90:
                # STORE NAME(namei)
                # name = TOS
                # namei is the index of name in the attribute co_names
                # FIXME potential issue with scoping
                add_lines([f"# STORE NAME {inst.argrepr}",
                           f"execute if data storage mcl:main co_names[{inst.arg}] run data modify storage mcl:main co_names[{inst.arg}] set from storage mcl:main stack[0][0]",
                           f"execute unless data storage mcl:main co_names[{inst.arg}] run data modify storage mcl:main co_names append from storage mcl:main stack[0][0]",
                           "data remove storage mcl:main stack[0][0]"])
            case 91:
                # DELETE NAME(namei)
                # del name
                # Where namei is the index into co_names attribute
                # FIXME potential issue with scoping
                add_lines([f"data remove storage mcl:main co_names[{inst.arg}]"])
            case 92:
                # UNPACK SEQUENCE(count)
                # assuming TOS is unpackable, unpacks and stores its elements on
                # the stack[0]
                # 1 2 3 4 5 -> 1a 1b 1c 1d 2 3 4 5
                print(92)
            case 93:
                # FOR ITER(delta)
                # TOS is an iterator
                # calls next(TOS) and pushes the result onto the stack[0]
                # if next(TOS) yields nothing, TOS is popped and byte code
                # counter is incremented by delta

                # pop top if iterator is empty
                add_lines(["# FOR ITER"])
                if inst.is_jump_target:
                    start_while(
                        "execute if data storage mcl:main stack[0][0].value[0] run")
                queue_end_on_instr(inst.arg + current_instr + 1)


                # push next value of iter to stack[0]
                add_lines(["# Pop first item if any from iterator and push it to the stack"])
                start_if(
                    "execute if data storage mcl:main stack[0][0].value[0] run")
                add_lines(["data modify storage mcl:main stack[0] prepend value {}",
                           "data modify storage mcl:main stack[0][0].value set from storage mcl:main stack[0][1].value[0]",
                           "data remove storage mcl:main stack[0][1].value[0]"])
                end()
            case 94:
                # UNPACK EX(counts)
                # TODO figure out how this works
                print(94)
            case 95:
                # STORE ATTR(namei)
                # TOS.name = TOS1
                # Where namei is the index of name in co_names
                print(95)
            case 96:
                # DELETE ATTR(namei)
                # del TOS.name
                # using namei as index into co_names
                print(96)
            case 97:
                # STORE GLOBAL(namei)
                # Works as STORE_NAME but in the global space
                print(97)
            case 98:
                # DELETE GLOBAL(namei)
                # works as DELETE_NAME but deletes a global name
                print(98)
            case 99:
                # ROT N(count)
                # lift the top count items and move TOS to position count
                # ROT 6:
                # 1 2 3 4 5 6 7 8 -> 2 3 4 5 6 7 1 8
                # FIXME potential off-by-one error here
                add_lines(
                    [f"data modify storage mcl:main stack[0] insert {inst.argval} from storage mcl:main stack[0][0]",
                     "data remove storage mcl:main stack[0][0]"])
            case 100:
                # LOAD CONST(consti)
                # pushes co_consts[consti] onto the stack[0]
                add_lines([f"# LOAD CONST {inst.argrepr}"])
                if type(inst.argval) == CodeType:
                    print("\033[94mCompiling embedded code object!\033[0m")
                    start_fn(inst.argval.co_name, inst.argval.co_argcount)
                    compile('', inst.argval)
                    end()
                    print("\033[94mFinished compiling embedded code object!\033[0m")
                else:
                    constants.append(inst.argval)
                    const = 0
                    arg_type = "None"
                    if type(inst.argval) == str:
                        arg_type = "str"
                        const = str(list(inst.argval))
                    elif type(inst.argval) == int or type(inst.argval) == float:
                        arg_type = "num"
                        const = numeric_to_value(inst.argval)
                    elif type(inst.argval) == list or type(inst.argval) == tuple:
                        arg_type = "list"
                        const = list_to_value(inst.argval)
                    add_lines([f'data modify storage mcl:main stack[0] prepend value {{value:{str(const)}, type:"{arg_type}"}}'])
            case 101:
                # LOAD NAME(namei)
                # pushes the value associated with co_names[namei] onto stack[0]
                if inst.argrepr not in GLOBALS:
                    if inst.argrepr in GLOBAL_METHODS:
                        add_lines([f"# LOAD METHOD {inst.argrepr}",
                               f'execute if data storage mcl:main co_names[{inst.arg}] run data modify storage mcl:main co_names[{inst.arg}] set value {{value:"{inst.argval}",type:"callable"}}',
                               f'execute unless data storage mcl:main co_names[{inst.arg}] run data modify storage mcl:main co_names append value {{value:"{inst.argval}",type:"callable"}}',
                               f'data modify storage mcl:main stack[0] prepend value {{value:"{inst.argval}",type:"callable"}}'])
                    else:
                        add_lines(
                        [f"# LOAD NAME {inst.argrepr}",
                        f"data modify storage mcl:main stack[0] prepend from storage mcl:main co_names[{inst.arg}]"])

            case 102:
                # BUILD TUPLE(count)
                # Creates a tuple consuming count items from the stack[0] and
                # pushes the resulting tuple onto the stack[0]
                # BUILD TUPLE(2)
                # 1 2 3 4 5 -> (1,2) 3 4 5
                warning("There is no distinction between tuples and lists in MCL")
                add_lines(
                    ["data modify storage mcl:main temp set value {}"])
                for _ in range(inst.argval):
                    add_lines(
                        ["data modify storage mcl:main temp append from storage mcl:main stack[0][0]",
                         "data remove storage mcl:main stack[0][0]"])
                remove_line()
                add_lines(
                    ["data modify storage mcl:main stack[0] prepend from storage mcl:main temp"])
            case 103:
                # BUILD LIST(count)
                # works the same as BUILD_TUPLE but creates a list
                if inst.argval:
                    add_lines(
                        [f"# BUILD LIST from top {inst.argval} values",
                         'data modify storage mcl:main temp set value {value:[],type:"list"}'])
                    for _ in range(inst.argval):
                        add_lines(
                            ["data modify storage mcl:main temp.value prepend from storage mcl:main stack[0][0]",
                            "data remove storage mcl:main stack[0][0]"])
                    remove_line()
                    add_lines(
                        ["# Push resulting list onto stack",
                        "data modify storage mcl:main stack[0][0] set from storage mcl:main temp"])
                else:
                    add_lines(["# BUILD EMPTY LIST",
                               'data modify storage mcl:main stack[0] prepend value {value:[], type:"list"}'])
            case 104:
                # BUILD SET(count)
                # works the same as BUILD TUPLE but builds a set
                warning("Sets have a complexity of O(n^2) to garuntee uniqueness. Use lists when possible")
                print(104)
            case 105:
                # BUILD MAP(count)
                # pushes a new dict onto the stack[0]
                # pops 2*count items so the dict holds count items:
                # BUILD_MAP(2):
                # 1 2 3 4 5 6 -> {4:3, 2:1} 5 6
                add_lines(
                    ["data modify storage mcl:main temp set value {dict:[]}"])
                for _ in range(inst.argval):
                    add_lines(
                        ["data modify storage mcl:main temp.dict append value {key:0,value:0}",
                         "data modify storage mcl:main temp.dict[-1].value set from storage mcl:main stack[0][0].value",
                         "data remove storage mcl:main stack[0][0]",
                         "data modify storage mcl:main temp.dict[-1].key set from storage mcl:main stack[0][0].value",
                         "data remove storage mcl:main stack[0][0]"])
                add_lines(["data modify storage mcl:main stack[0] prepend value []",
                           "data modify storage mcl:main stack[0][0] append from storage mcl:main temp"])
            case 106:
                # LOAD_ATTR(namei)
                # Replace TOS with getattr(TOS, co_names[namei])
                print(106)
            case 107:
                # COMPARE_OP(opname)
                # performs boolean operation
                match inst.argval:
                    case '==':
                        add_lines(
                            ["# COMPARE TOS1 == TOS",
                             "data modify storage mcl:main temp set from storage mcl:main stack[0][0]",
                             "data remove storage mcl:main stack[0][0]",
                             "execute store success score #mcl mcl0 run data modify storage mcl:main temp set from storage mcl:main stack[0][0]",
                             "data remove storage mcl:main stack[0][0]"])
                    case '<=':
                        pass
                    case '>=':
                        pass
                    case '>':
                        pass
                    case '<':
                        pass
                    case '!=':
                        pass
            case 108:
                # IMPORT NAME
                # meta
                pass
            case 109:
                # IMPORT FROM
                # meta
                pass
            case 110:
                # JUMP FORWARD(delta)
                # increases bytecode counter by delta

                # ! must be achieved via other means
                pass
            case 111:
                # JUMP IF FALSE OR POP(target)
                # if TOS is false, sets the bytecode counter to target and
                # leaves TOS on the stack[0]
                # Otherwise e.g. TOS is true, TOS is popped
                # ! must be achieved via other means
                pass
            case 112:
                # JUMP IF TRUE OR POP(target)
                # if TOS is true, sets the bytecode counter to target and
                # leaves TOS on the stack[0]
                # Otherwise e.g. TOS is false, TOS is popped
                # ! must be achieved via other means
                pass
            case 113:
                # JUMP ABSOLUTE(target)
                # set bytecode counter to target
                # ! must be achieved via other means. THIS CURRENTLY IS ONLY THE END OF A FOR-LOOP
                pass
            case 114:
                # POP JUMP IF FALSE(targer)
                # if TOS is false, sets the byte counter to target
                # TOS is popped.
                add_lines(["# POP JUMP IF FALSE"])
                start_if("execute if score #mcl mcl0 matches 0 run")
                queue_end_on_instr(inst.arg)
            case 115:
                # POP JUMP IF TRUE(targer)
                # if TOS is true, sets the byte counter to target
                # TOS is popped.
                add_lines(["# POP JUMP IF TRUE"])
                start_if("execute unless score #mcl mcl0 matches 0 run")
                queue_end_on_instr(inst.arg)
            case 116:
                # LOAD GLOBAL(namei)
                # loads the global named co_names[namei] onto the stack[0]
                add_lines(
                    [f"data modify storage mcl:main stack[0] prepend from storage mcl:main co_names[{inst.arg}]"])
            case 117:
                # IS OP(invert)
                # performs `is` comparison, or `is not` if invert is 1
                not_implemented('`is` keyword', current_line)
            case 118:
                # CONTAINS OP(invert)
                # performs `in` comparison, or `not in` if invert is 1
                print(118)
            case 119:
                # RERAISE
                # Re-raises the exception currently on top of the stack[0].
                not_implemented('error handling', current_line)

            case 121:
                # JUMP IF NOT EXC MATCH(target)
                # tests whether the second value on the stack[0] is an exception
                # matching TOS, and jumps if not.
                # Pops 2
                not_implemented('error handling', current_line)
            case 122:
                # SETUP FINALLY(delta)
                not_implemented('error handling', current_line)

            case 124:
                # LOAD FAST(var_num)
                # Pushes a reference to the local co_varnames[var_num]
                # onto the stack[0]
                print(124)
            case 125:
                # STORE FAST(var_num)
                # Stores TOS into the local co_varnames[var_num]
                print(125)
            case 126:
                # DELETE_FAST(var_num)
                # Deletes local co_varnames[var_num]
                print(126)

            case 129:
                # GEN START(kind)
                not_implemented('error handling', current_line)
            case 130:
                # RAISE VARARGS
                not_implemented('error handling', current_line)
            case 131:
                # CALL FUNCTION(argc)
                # calls a callable object with positional args.
                # argc indicates the number of positional args.
                # The TOS contains positional arguments, with the right-most
                # argument on top.
                # Below the arguments is a callable object to call
                # CALL FUNCTION pops all arguments and the callable object
                # off the stack[0], calls the callable object with those args,
                # and pushes the returned value to the stack[0]
                if (fn := prev_calls[-inst.arg - 1].argval) in GLOBALS:
                    match fn:
                        case 'print':
                            add_lines(["# format TOS into string if TOS is a number"])
                            start_if(
                                'execute if data storage mcl:main stack[0][0].value.num run')
                            add_lines(
                                ["data modify storage mcl:main temp set value [[]]",
                                 "data modify storage mcl:main temp append from storage mcl:main stack[0][0].value.num"])
                            start_while(
                                "execute if data storage mcl:main temp[1][0] run")
                            add_lines(
                                ["execute store result entity @e[type=marker,tag=read_head,limit=1] Pos[0] double 1 run data get storage mcl:main temp[1][0] 1",
                                 "execute at @e[type=minecraft:marker,limit=1,tag=read_head] run data modify storage mcl:main temp[0] append from block ~ ~ ~ Items[0].tag.num_to_str",
                                 "data remove storage mcl:main temp[1][0]"])
                            end()
                            add_lines(["data modify storage mcl:main stack[0][0].value set from storage mcl:main temp[0]"])
                            end()
                            add_lines(['# PRINT',
                                       'tellraw @p {"nbt":"stack[0][0].value","storage":"mcl:main","interpret":true}'])
                        case 'str':
                            add_lines(
                                ["# format TOS into string if TOS is a number"])
                            start_if(
                                'execute if data storage mcl:main stack[0][0].value.num run')
                            add_lines(
                                ["data modify storage mcl:main temp set value [[]]",
                                 "data modify storage mcl:main temp append from storage mcl:main stack[0][0].value.num"])
                            start_while(
                                "execute if data storage mcl:main temp[1][0] run")
                            add_lines(
                                ["execute store result entity @e[type=marker,tag=read_head,limit=1] Pos[0] double 1 run data get storage mcl:main temp[1][0] 1",
                                 "execute at @e[type=minecraft:marker,limit=1,tag=read_head] run data modify storage mcl:main temp[0] append from block ~ ~ ~ Items[0].tag.num_to_str",
                                 "data remove storage mcl:main temp[1][0]"])
                            end()
                            end()
                elif (fn := prev_calls[-inst.arg - 1].argval) in GLOBAL_METHODS:
                    add_lines(
                        ["# CALL GLOBAL METHOD",
                         "data modify storage mcl:main temp set value {callable:{}, instance:{}}",
                         f"data modify storage mcl:main temp.instance set from storage mcl:main stack[0][0]",
                         f"data remove storage mcl:main stack[0][0]"])

                    add_lines(
                        ["data modify storage mcl:main temp.callable set from storage mcl:main stack[0][0]",
                            "data remove storage mcl:main stack[0][0]"])
                    add_lines(["function mcl:util/method_invoker"])

                else:
                    add_lines(
                        ["# CALL FUNCTION",
                        "data modify storage mcl:main temp set value {args:[], callable:{}}"])

                    for _ in range(inst.argval):
                        add_lines(["data modify storage mcl:main temp.args append from storage mcl:main stack[0][0]",
                                "data remove storage mcl:main stack[0][0]"])
                    # the args and callable are now stored in temp[] with temp[-1] being the callable

                    add_lines(
                        ["data modify storage mcl:main temp.callable set from storage mcl:main stack[0][0]",
                        "data remove storage mcl:main stack[0][0]",
                        "data modify storage mcl:main stack prepend value []"])
                    for _ in range(inst.arg):
                        add_lines(["data modify storage mcl:main stack[0] prepend from storage mcl:main temp.args[-1]",
                                   "data remove storage mcl:main temp.args[-1]"])
                    add_lines(["function mcl:util/invoker"])
            case 132:
                # MAKE FUNCTION(flags)
                # Pushes a new function object on the stack[0]
                # From bottom to top, the consumed stack[0] must consist of values
                # if the argument carries a specified value flag
                #   0x01 a tuple or default values for positional-only and
                # positional-or-keyword params in positional order
                #   0x02 a dict of keyword-only params' default values
                #   0x04 a tuple of strings containg the param's annotations
                #   0x08 a tuple containing the cells for free variables,
                # making a closure
                # the code associated with the function (at TOS1)
                # the qualified name of the function (at TOS)

                # this should be the name of the function
                Function.active.lines.pop()
                Function.active.lines.pop()
                add_lines(["# MAKE FUNCTION",
                           f'data modify storage mcl:main stack[0] prepend value {{value:"{prev_calls[-1].argval}", type:"callable"}}'])
                add_fn(constants[-1])
            case 133:
                # BUILD SLICE(argc)
                not_implemented('slicing', current_line)

            case 135:
                # LOAD CLOSURE(i)
                # pushes a reference to the cell contained in slot i of the cell
                # and free variable storage. The name of the variable is
                # co_cellvars[i] if i is less than len(co_cellvars)]
                # Otherwise, it is co_freevars[i-len(co_cellvars)]
                # TODO what even the fuck
                print(135)
            case 136:
                # LOAD DREF(i)
                # Loads the cell contained in slot i of the cell and free
                # variable storage
                # Pushes a ref to the object the cell contains on the stack[0]
                # TODO what even the fuck
                print(136)
            case 137:
                # STORE DREF(i)
                # Stores TOS into the cell contained in slot i of the cell and
                # free variable storage
                print(137)
            case 138:
                # DELETE DREF(i)
                # Empties the cell contained in slot i of the cell and free
                # variable storage
                # Used by the del statement
                print(138)

            case 141:
                # CALL_FUNCTION_KW(argc)
                # alls a callable object with positional (if any) and keyword
                # arguments.
                # argc indicates the total number of positional and keyword
                # arguments.
                # The top element on the stack[0] contains a tuple with the names
                # of the keyword arguments, which must be strings.
                # Below that are the values for the keyword arguments,
                # in the order corresponding to the tuple.
                # Below that are positional arguments, with the right-most
                # parameter on top.
                # Below the arguments is a callable object to call.
                # CALL_FUNCTION_KW pops all arguments and the callable object
                # off the stack[0], calls the callable object with those arguments,
                # and pushes the return value returned by the callable object.
                print(141)
            case 142:
                # CALL FUNCTION EX(flags)
                # Calls a callable object with variable set of positional and
                # keyword arguments.
                # If the lowest bit of flags is set, the top of the stack[0]
                # contains a mapping object containing additional keyword
                # arguments.
                # Before the callable is called, the mapping object and iterable
                # object are each “unpacked” and their contents passed in as
                # keyword and positional arguments respectively.
                # CALL_FUNCTION_EX pops all arguments and the callable object
                # off the stack[0], calls the callable object with those arguments,
                # and pushes the return value returned by the callable object
                print(142)
            case 143:
                not_implemented('`with` blocks', current_line)
            case 144:
                # EXTENDED ARG(ext)
                # Prefixes any opcode which has an argument too big to fit into
                # one byte
                # TODO loop through and implement these before compilation
                # NOTE EXTENDED ARG can be chained up to 3 times, allowing up to
                # 4 bytes
                print(144)
            case 145:
                # LIST APPEND(i)
                # list.append(TOS1[-i], TOS)
                add_lines(
                    [f"data modify storage mcl:main stack[0][1].value[{-inst.argval}] append from storage mcl:main stack[0][0].value"])
                print(145)
            case 146:
                # SET ADD(i)
                # set.add(TOS1[-i], TOS)
                print(146)
            case 147:
                # MAP ADD(i)
                # dict.__setitem__(TOS1[-i], TOS1, TOS)
                print(147)
            case 148:
                # LOAD CLASSDEREF(i)
                # Much like LOAD_DEREF but first checks the locals dictionary
                # before consulting the cell
                # This is used for loading free variables in class bodies
                print(148)

            case 152:
                # MATCH CLASS
                # TOS is a tuple of keyword attribute names, TOS1 is the class
                # being matched against, and TOS2 is the match subject
                # count is the number of positional sub-patterns
                #
                # Pop TOS. If TOS2 is an instance of TOS1 and has the positional
                # and keyword attributes required by count and TOS,
                # set TOS to True and TOS1 to a tuple of extracted attributes
                # Otherwise, set TOS to False.
                print(152)

            case 154:
                # SETUP ASYNC WITH
                not_implemented('async behavior', current_line)
            case 155:
                # FORMAT VALUE(flags)
                # Used for implementing formatted literal strings (f-strings)
                # Pops an optional fmt_spec from the stack[0],
                # then a required value.
                # flags is interpreted as follows:
                #   (flags & 0x03) == 0x00: value is formatted as-is
                #   (flags & 0x03) == 0x01: call str() on value before
                # formatting it
                #   (flags & 0x03) == 0x02: call repr() on value before
                # formatting it
                #   (flags & 0x03) == 0x03: call ascii() on value before
                # formatting it
                #   (flags & 0x04) == 0x04: pop fmt_spec from the stack[0] and use
                # it, else use an empty fmt_spec
                #
                # Formatting is performed using PyObject_Format()
                # The result is pushed on the stack[0].
                if inst.argval == 0x00:
                    pass
                print(155)
            case 156:
                # BUILD CONST KEY MAP(count)
                # The version of BUILD_MAP specialized for constant keys
                # Pops the top element on the stack[0] which contains a tuple of
                # keys, then starting from TOS1, pops count values to form
                # values in the built dictionary.
                print(156)
            case 157:
                # BUILD STRING(count)
                # Concatenates count strings from the stack[0] and pushes the
                # resulting string onto the stack[0]
                print(157)

            case 160:
                # LOAD METHOD(namei)
                # Loads a method named co_names[namei] from the TOS object
                # TOS is popped
                # This bytecode distinguishes two cases:
                # if TOS has a method with the correct name,
                # the bytecode pushes the unbound method and TOS
                # TOS will be used as the first argument (self) by CALL_METHOD
                # when calling the unbound method
                # Otherwise, NULL and the object return by the attribute lookup
                # are pushed.
                add_lines(["# LOAD METHOD",
                           f'execute if data storage mcl:main co_names[{inst.arg}] run data modify storage mcl:main co_names[{inst.arg}] set value {{value:"{inst.argval}",type:"callable"}}',
                           f'execute unless data storage mcl:main co_names[{inst.arg}] run data modify storage mcl:main co_names append value {{value:"{inst.argval}",type:"callable"}}',
                           f'data modify storage mcl:main stack[0] prepend value {{value:"{inst.argval}",type:"callable"}}'])
            case 161:
                # CALL METHOD(argc)
                # Calls a method
                # argc is the number of positional arguments
                # Keyword arguments are not supported
                # This opcode is designed to be used with LOAD_METHOD
                # Positional arguments are on top of the stack[0]
                # Below them, the two items described in LOAD_METHOD are on the
                # stack[0] (either self and an unbound method object or NULL and an
                # arbitrary callable)
                # All of them are popped and the return value is pushed
                add_lines(
                    ["# CALL METHOD",
                         "data modify storage mcl:main temp set value {args:[], callable:{}, instance:{}}",
                         f"data modify storage mcl:main temp.instance set from storage mcl:main stack[0][{inst.argval + 1}]",
                         f"data remove storage mcl:main stack[0][{inst.argval + 1}]"])

                for _ in range(inst.argval):
                    add_lines(["data modify storage mcl:main temp.args append from storage mcl:main stack[0][0]",
                                "data remove storage mcl:main stack[0][0]"])
                # the args and callable are now stored in temp[] with temp[-1] being the callable

                add_lines(
                    ["data modify storage mcl:main temp.callable set from storage mcl:main stack[0][0]",
                        "data remove storage mcl:main stack[0][0]"])
                add_lines(["function mcl:util/method_invoker"])
                add_lines([f"# save to pointer",
                           f"data modify storage mcl:main co_names[{prev_calls[-(inst.arg + 2)].arg}] set from storage mcl:main stack[0][0]"])
            case 162:
                # LIST EXTEND(i)
                # Calls list.extend(TOS1[-i], TOS)
                # Used to build lists
                print(162)
            case 163:
                # SET UPDATE(i)
                # Calls set.update(TOS1[-i], TOS)
                # Used to build sets
                print(163)
            case 164:
                # DICT MERGE
                # Like DICT_UPDATE but raises an exception for duplicate keys
                print(164)
            case 165:
                # DICT_UPDATE(i)
                # Calls dict.update(TOS1[-i], TOS)
                # Used to build dicts
                print(165)
        prev_calls.append(inst)

compile('./script.py')

for f in Function.functions:
    if f.name in ['tick']:
        print(f.name)
        f.lines.pop()
        f.lines.pop()
        f.lines.pop()
        f.lines.pop()

print(Function.functions)

if WRITE_DATAPACK:
    with open(WRITE_DIR + '\\tick.mcfunction', 'w') as outfile:
        outfile.write('')
    for f in Function.functions:
        with open(WRITE_DIR + '\\' + f.name + '.mcfunction', 'w') as outfile:
            outfile.write(repr(f))
