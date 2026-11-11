"""Android bridge for the original BANGLADESH BHASHA compiler and VM."""

MAX_SOURCE_SIZE = 1_000_000


def get_status():
    try:
        from bb import compile_source
        from runtime.vm import VirtualMachine

        return (
            "BANGLADESH BHASHA Android Runtime: READY\n"
            "Original Compiler: CONNECTED\n"
            "Original Virtual Machine: CONNECTED\n"
            "Offline execution: AVAILABLE"
        )
    except Exception as error:
        return (
            "Android Runtime: STARTED\n"
            "Compiler integration: ERROR\n"
            + str(error)
        )


def run_source(source):
    if not isinstance(source, str):
        return "ERROR: Source must be text."

    if not source.strip():
        return "ERROR: Empty source file."

    if len(source) > MAX_SOURCE_SIZE:
        return "ERROR: Source file exceeds the size limit."

    try:
        from bb import compile_source
        from runtime.vm import VirtualMachine

        bytecode = compile_source(source)
        vm = VirtualMachine()
        results = vm.run(bytecode)

        if not results:
            return "প্রোগ্রাম সফলভাবে সম্পন্ন হয়েছে।\nকোনো Output নেই।"

        return "\n".join(str(item) for item in results)

    except Exception as error:
        return "BHASHA ERROR:\n" + str(error)
