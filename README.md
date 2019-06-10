**CmdRunner** is a modular command encoder used to easily encode data run through various systems and commands. It's primary use is to run commands on remote systems accessed through multiple hops.

![Asciinema Screencast](/docs/demo.gif)

# Usage
CmdRunner commands are all prefixed with `$`, any commands without this prefix will be sent down the encoding pipeline to the configured command runner.

```shell
>>> $help
Available commands:
        $list_decoders        List available output decoders
        $list_encoders        List available command encoders
        $list_runners         List available command runners
        $load_session         Load session from saved json file
        $pop_decoder          Remove decoder from decoders list
        $pop_encoder          Remove encoder from encoders list
        $print_session        Print session information
        $push_decoder         Add a decoder to the decoders list
        $push_encoder         Add an encoder to the encoders list
        $quit                 Quit CmdRunner
        $save_session         Save session data to json file
        $set_runner           Set the command runner

For help on individual modules use "$help <module_type> <module>", e.g.:
        $help runner bash
        $help encoder xpcmdshell
        $help decoder base64
```

# Extending
CmdRunner can be easily extended by implementing `runner`, `encoder` and `decoder` modules, see the various directories in `lib/*` for examples.
