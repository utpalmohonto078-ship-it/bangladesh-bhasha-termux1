# Fresh V2 status

## Implemented

- Lexer, AST nodes and Pratt expression parser
- Semantic variable and scope checks
- IR generation and bytecode validation
- Stack-based virtual machine
- Bengali and English syntax
- Variables, arithmetic, comparisons and booleans
- IF / ELSE branches
- REPEAT loops and nested REPEAT
- WHILE loops
- Nested WHILE loops
- WHILE with IF / ELSE
- Functions, recursion and argument-count checks
- RETURN
- GLOBAL, including nested IF / ELSE / REPEAT / WHILE blocks
- Builtins: type detection (ধরন / type_of), string length (দৈর্ঘ্য / length), with argument-count checks
- BREAK / CONTINUE (থামো / চালিয়ে_যাও) in WHILE and REPEAT, with compile-time check for use outside loops
- Top-level initializer ordering check (use-before-declare is a compile-time NameError)

## Verified tests

- V2 regression tests: 41 passing
- Advanced WHILE standalone checks: 3 passing
- V1 multilingual tests: 8 passing
- V1 negative tests: 13 passing

The standalone advanced WHILE checks are also included in the permanent V2 test suite.

## Not yet implemented in V2

- Collections (lists, maps) and more string builtins
- Input builtin
- Exception handling
- Classes and object-oriented programming
- Modules and package manager
- Standard library
- REPL and debugger
- Sandboxing and native compilation
- Web development and database modules
- Defensive cybersecurity and digital forensics modules

This is a tested development foundation, not a production release.

## Static Type System — First Version
- Static type checker: compiler/type_checker.py
- Integer, float, string, boolean ও unknown type inference
- Arithmetic ও string concatenation যাচাই
- Assignment compatibility যাচাই
- IF ও WHILE Boolean condition যাচাই
- REPEAT numeric count যাচাই
- Comparison compatibility যাচাই
- Builtin return type inference
- Type System tests: 8
- সর্বশেষ সম্পূর্ণ test suite: 49/49 PASS
- বাকি: Function parameter ও return type validation

## নির্মাতা ও প্রকল্পের স্বীকৃতি

- **নির্মাতা:** উৎপল কুমার মোহন্ত
- **ঠিকানা:** তুষভান্ডার, কালীগঞ্জ, লালমনিরহাট, রংপুর, বাংলাদেশ
- **YouTube:** https://youtube.com/@utpalmohontochoton
- **GitHub:** https://github.com/utpalmohonto078-ship-it
