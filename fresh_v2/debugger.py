from pathlib import Path

from bb import compile_source
from runtime.vm import VirtualMachine


class DebuggerStopped(Exception):
    pass


def run_debugger(program, command_fn=input, output_fn=print):
    vm = VirtualMachine()
    running = False

    def trace(ip, instruction, machine):
        nonlocal running

        if running:
            return

        output_fn(f"\n[IP {ip}] {instruction}")

        while True:
            command = command_fn(
                "debug (step/continue/vars/stack/quit)> "
            ).strip().lower()

            if command in ("s", "step"):
                return

            if command in ("c", "continue"):
                running = True
                return

            if command in ("v", "vars"):
                output_fn(f"Global variables: {machine.variables}")
                if machine.frames:
                    output_fn(
                        f"Local variables: {machine.frames[-1]['locals']}"
                    )
                continue

            if command in ("stack", "st"):
                output_fn(f"Stack: {machine.stack}")
                continue

            if command in ("q", "quit", "exit"):
                raise DebuggerStopped()

            if command in ("h", "help"):
                output_fn("step | continue | vars | stack | quit")
                continue

            output_fn("অজানা কমান্ড। help লিখুন।")

    try:
        vm.run(program, trace_fn=trace)
    except DebuggerStopped:
        output_fn("Debugger বন্ধ করা হয়েছে।")
        return False

    output_fn("\n===== PROGRAM OUTPUT =====")
    for result in vm.output:
        output_fn(str(result))

    output_fn("===== DEBUG SESSION FINISHED =====")
    return True


def debug_file(path):
    source = Path(path).read_text(encoding="utf-8")
    program = compile_source(source)
    return run_debugger(program)
