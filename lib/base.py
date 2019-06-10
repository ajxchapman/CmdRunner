import readline

class CmdRunnerException(Exception):
    pass

class CmdArgument:
    _index = 0

    def __init__(self, default=None, arg_type=None, required=None, description=None):
        self.default = default
        self.arg_type = arg_type or type(default)
        if default is None and arg_type is None:
            raise CmdRunnerException("Must specify a type for non default arguments")
        if self.arg_type not in [int, str, bytes, bool, type(None)]:
            raise CmdRunnerException("Unsupported argument type '{}'".format(self.arg_type))
        self.required = (default is None) if required is None else required
        self.description = description
        self._index = CmdArgument._index
        CmdArgument._index += 1

class CmdBase:
    def __init__(self, *args, **kwargs):
        """
        Permissive __init__ method to assign object attributes from vrious sources:
          <args> matching the order of the <cls.args> attribute
          <kwargs> assigning each key, value pair as attributes
          <cls.default_args> assign each unset key, value pair as default attributes
        """
        def set_argument(name, arg, value):
            if value != arg.default:
                if not isinstance(value, arg.arg_type):
                    raise TypeError("Incorrect argument type for argument '{}', expecting '{}' receivied '{}'".format(name, arg.arg_type.__name__, type(value).__name__))
            setattr(self, name, value)

        cmd_arguments = {k : v for k, v in self.__class__.__dict__.items() if isinstance(v, CmdArgument)}
        sorted_arguments = sorted(cmd_arguments.keys(), key=lambda x: cmd_arguments[x]._index)
        required_arguments = [k for k in cmd_arguments.keys() if cmd_arguments[k].required]

        # Assign arguments based on the class args variable
        for index, arg in enumerate(sorted_arguments):
            if index >= len(args):
                break
            set_argument(arg, cmd_arguments[arg], args[index])

        # Assign all kwargs
        for k, v in kwargs.items():
            if k in cmd_arguments:
                if not isinstance(getattr(self, k), CmdArgument):
                    raise TypeError("Argument repeated '{}' value '{}'".format(k, getattr(self, k)))
                set_argument(k, cmd_arguments[k], v)

        # Assign all default values
        for k, v in cmd_arguments.items():
            if v.default or not v.required:
                if isinstance(getattr(self, k), CmdArgument):
                    set_argument(k, v, v.default)

        # Check all required arguments exist
        for arg in required_arguments:
            if isinstance(getattr(self, arg), CmdArgument):
                raise TypeError("Missing required argument '{}'".format(arg))

        # Check no unnecessary arguments were provided
        if len(args) > len(cmd_arguments):
            raise TypeError("Constructor takes {} positional arguments but {} were given".format(len(cmd_arguments), len(args)))
        for x in kwargs.keys():
            if not x in sorted_arguments:
                raise TypeError("Constructor got an unexpected keyword argument '{}'".format(x))

    @classmethod
    def get_subclasses(cls):
        def _subclasses(cls):
            return set(cls.__subclasses__()).union([s for c in cls.__subclasses__() for s in _subclasses(c)])
        return _subclasses(cls)

    @classmethod
    def get_help(cls):
        lines = []
        for index, line in enumerate(cls.help.strip("\n").splitlines()):
            if index == 0:
                padding = line.replace(line.lstrip(), "")
            lines.append(line.replace(padding, "", 1))
        return "\n".join(lines).strip()

    @classmethod
    def get_args(cls):
        reqcmdline = []
        optcmdline = []
        arg_help = ""
        for arg_name in sorted([k for k, v in cls.__dict__.items() if isinstance(v, CmdArgument)], key=lambda x: cls.__dict__[x]._index):
            arg = getattr(cls, arg_name)
            if arg.required:
                reqcmdline.append("<{}>".format(arg_name))
            else:
                optcmdline.append("[--{}=<{}>]".format(arg_name, arg.arg_type.__name__))
            arg_help += "\n\t{:20s} {:5s} {:20s} {}".format(arg_name, arg.arg_type.__name__, "default={}".format(arg.default) if arg.default else "", arg.description)
        return "{} {}{}".format(cls.__name__, " ".join(optcmdline + reqcmdline), arg_help)


    def get_instance(self):
        output = [self.__class__.__name__]
        for arg in sorted([k for k, v in self.__class__.__dict__.items() if isinstance(v, CmdArgument)], key=lambda x: self.__class__.__dict__[x]._index):
            output.append("\t{}: {}".format(arg, str(getattr(self, arg))))
        return "\n".join(output)

    def save(self):
        output = {"__classname__" : self.__class__.__name__}
        for arg in self.args or [x for x in sorted(self.__dict__.keys()) if not x.startswith("_")]:
            output[arg] = getattr(self, arg)
        return output

    @classmethod
    def load(cls, instance):
        return cls(**instance)

class CmdRunner(CmdBase):
    def encode(self, cmd):
        return cmd

class CmdEncoder(CmdBase):
    help = """
    Basic command encoder.
    """

    def encode(self, cmd):
        """
        Simple CmdEncoder which just returns the command as is.
        """
        return cmd

    def ready(self, index, encoders):
        pass

class CmdDecoder(CmdBase):
    def decode(self, cmd):
        """
        Simple CmdDecoder which just returns the command output as is.
        """
        return cmd

class InteractiveCmd(CmdBase):
    tag = None
    description = "InteractiveCmd base class"
    tab_complete_options = []

    @classmethod
    def get_command(cls, cmd):
        cmd = cmd.lstrip("$")
        clsses = cls.get_subclasses()
        index = 1
        while len(clsses) > 1:
            if index > len(cmd):
                raise CmdRunnerException("Ambiguous command '{}', did you mean {}".format(cmd, ", ".join("'{}'".format(x.tag) for x in clsses)))
            for cls in list(clsses):
                if not cls.tag.startswith(cmd[:index]):
                    clsses.remove(cls)
            index += 1
        if len(clsses) == 0:
            raise CmdRunnerException("Unknown command '{}'".format(cmd))
        return list(clsses)[0]

    @classmethod
    def parse_cmd(cls):
        pass

    @classmethod
    def completer(cls, text, state):
        line = readline.get_line_buffer()
        if line.startswith("$"):
            parts = line.lstrip("$").split(" ")
            subclsses = cls.get_subclasses()
            options = []
            if len(parts) > 1:
                for subcls in subclsses:
                    if subcls.tag == parts[0]:
                        options = subcls.tab_complete_options
                        break
                if any(x in options for x in parts[1:]):
                    return None
            else:
                options = ["{} ".format(x.tag) for x in subclsses]
            try:
                return [x for x in options if x.lower().startswith(text.lower())][state]
            except IndexError:
                pass
        return None

def execute(cmd, session):
    for index, encoder in enumerate(session["encoders"]):
        encoder.ready(index, session["encoders"])
    for encoder in session["encoders"][::-1]:
        cmd = encoder.encode(cmd)
    cmd = session["runner"].encode(cmd)
    output = session["runner"].run(cmd)
    for decoder in session["decoders"][::-1]:
        output = decoder.decode(output)
    return output
