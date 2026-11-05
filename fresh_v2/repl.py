from bb import compile_source, run_source

def main():
    print("==================================================")
    print("      BANGLADESH BHASHA INTERACTIVE REPL         ")
    print("==================================================")
    print("Type 'exit' or 'quit' to exit the shell.\n")

    while True:
        try:
            line = input("বাংলা-ভাষা> ")
            if line.strip().lower() in ["exit", "quit"]:
                print("বিদায়!")
                break
            if not line.strip():
                continue

            results = run_source(line + "\n")
            if results is not None:
                for res in results:
                    print(res)

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
