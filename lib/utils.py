import ast
import io
import json
import tokenize

class ArgsException(Exception):
    pass

def tokenize_args(argument_string):
    try:
        stack = {"[]": 0, "{}": 0}
        argument = []
        for token in tokenize.tokenize(io.BytesIO(argument_string.encode()).readline):
            if not token.type in [tokenize.NAME, tokenize.OP, tokenize.STRING, tokenize.NUMBER]:
                continue
            if token.type == tokenize.OP:
                if token.string in "[]":
                    stack["[]"] += 1 if token.string == "[" else -1
                elif token.string in "{}":
                    stack["{}"] += 1 if token.string == "{" else -1
                elif token.string == ",":
                        continue
                argument.append(token)
                if sum(stack.values()) == 0 and token.string in "]}":
                    yield argument_string[argument[0].start[1] : argument[-1].end[1]]
                    argument.clear()
            elif sum(stack.values()) == 0:
                argument.append(token)
                yield argument_string[argument[0].start[1] : argument[-1].end[1]]
                argument.clear()
        if len(argument):
            yield argument_string[argument[0].start[1] : argument[-1].end[1]]
    except tokenize.TokenError:
        raise ArgsException("Invalid arguments")

def get_args(argument_string):
    args = []
    kwargs = {}
    # Attempt json decoding of arguments
    try:
        output = json.loads(argument_string)
        if isinstance(output, dict):
            return [], output
    except json.decoder.JSONDecodeError:
        pass
    # Attempt command line and python calling decoding of arguments
    if argument_string.startswith("(") and argument_string.endswith(")"):
        argument_string = argument_string[1:-1]
    key = None
    tokens = list(tokenize_args(argument_string))
    for index, value in enumerate(tokens):
        try:
            if key is None:
                # Assign tokens of --key to the key variable and continue to process the next argument
                if value.startswith("-"):
                    key = value.lstrip("-")
                    continue
                # If the next token begins with =, this token is a key
                elif (index + 1) < len(tokens) and tokens[index + 1].startswith("="):
                    key = value
                    continue
            # Clean up tokens which start with '=', e.g. --key=value will tokenize to '--key', '=value'
            if value.startswith("="):
                value = value[1:]
            # Check key is a valid python variable name
            if key is not None and (key[0].isdigit() or not all(x.isalpha() or x.isdigit() or x == "_" for x in key)):
                raise ArgsException("Invalid keyword name '{}'".format(key))
            # Convert to python type if value is not a string
            if not value[0].isalpha():
                value = ast.literal_eval(value)
            else:
                value = {"true" : True, "false" : False, "none" : None}.get(value.lower(), value)
            if key is not None:
                kwargs[key] = value
            else:
                args.append(value)
        except ValueError:
            raise ArgsException("Invalid argument '{}'".format(arg))
        # Reset key to None, this can be bypassed using continue statement above
        key = None
    return args, kwargs
