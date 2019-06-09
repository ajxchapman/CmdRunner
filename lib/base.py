class CmdRunnerException(Exception):
    pass

class CmdBase:
    args = []
    default_args = {}

    def __init__(self, *args, **kwargs):
        """
        Permissive __init__ method to assign object attributes from vrious sources:
          <args> matching the order of the <cls.args> attribute
          <kwargs> assigning each key, value pair as attributes
          <cls.default_args> assign each unset key, value pair as default attributes
        """
        # Assign arguments based on the class args variable
        for index, arg in enumerate(self.args):
            if index >= len(args):
                break
            setattr(self, arg, args[index])

        # Assign all kwargs
        for k, v in kwargs.items():
            if not k.startswith("_"):
                setattr(self, k, v)

        # Assign all default values
        for k, v in self.default_args.items():
            try:
                getattr(self, k)
            except AttributeError:
                setattr(self, k, v)

        # Check all required arguments exist
        for arg in self.args:
            try:
                getattr(self, arg)
            except AttributeError:
                raise TypeError("{} Missing required argument '{}'".format(self.__class__.__name__, arg))

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

    def get_instance(self):
        output = [self.__class__.__name__]
        for arg in self.args:
            output.append("\t{}: {}".format(arg, str(getattr(self, arg))))
        for arg in [x for x in sorted(self.__dict__.keys()) if not x.startswith("_")]:
            if arg in self.args:
                continue
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
