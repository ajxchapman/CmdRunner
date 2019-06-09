import tokenize
import ast
import io

class ArgsException(Exception):
    pass

def get_args(argument_string):
    def _tokenize(argument_string):
        try:
            stack = {"()": 0, "[]": 0, "{}": 0}
            argument = []
            for token in tokenize.tokenize(io.BytesIO(argument_string.encode()).readline):
                if not token.type in [tokenize.NAME, tokenize.OP, tokenize.STRING, tokenize.NUMBER]:
                    continue
                if token.type == tokenize.OP:
                    if token.string in "()":
                        stack["()"] += 1 if token.string == "(" else -1
                    elif token.string in "[]":
                        stack["[]"] += 1 if token.string == "[" else -1
                    elif token.string in "{}":
                        stack["{}"] += 1 if token.string == "{" else -1
                    elif token.string == ",":
                        if sum(stack.values()) == 0:
                            yield argument_string[argument[0].start[1] : argument[-1].end[1]]
                            argument.clear()
                            continue
                argument.append(token)
            yield argument_string[argument[0].start[1] : argument[-1].end[1]]
        except tokenize.TokenError:
            raise ArgsException("Invalid arguments")
    args = []
    kwargs = {}
    for arg in _tokenize(argument_string):
        try:
            if not arg.startswith("\"") and "=" in arg:
                k, v = arg.split("=", 1)
                if k[0].isdigit() or not all(x.isalpha() or x.isdigit() or x == "_" in alphabet for x in k):
                    raise ArgsException("Invalid keyword name '{}'".format(k))
                kwargs[k] = ast.literal_eval(v)
            else:
                args.append(ast.literal_eval(arg))
        except ValueError:
            raise ArgsException("Invalid argument '{}'".format(arg))
    return args, kwargs
