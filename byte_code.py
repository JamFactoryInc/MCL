import dis

def get_bytecode(filename : str) -> dis.Bytecode:
    # get source code from module and compile
    with open(filename, 'r', encoding='utf-8') as infile:
        code = compile(source=infile.read(), filename=filename, mode='exec')

    # retrieve bytecode from compiled source
    return dis.Bytecode(code)

get_bytecode('./script.py')
