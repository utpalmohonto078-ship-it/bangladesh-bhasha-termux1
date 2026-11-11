# BANGLADESH BHASHA — ULTIMATE

বাংলা ভাষাভিত্তিক প্রোগ্রামিং ভাষা, কম্পাইলার, রানটাইম এবং বাংলা শিক্ষামূলক উপকরণ।

প্রকল্পের অগ্রগতি: [docs/STATUS.md](docs/STATUS.md)
শিক্ষা উপকরণ: [learning/README.md](learning/README.md)


## নির্মাতা ও প্রকল্পের স্বীকৃতি

- **নির্মাতা:** উৎপল কুমার মোহন্ত
- **ঠিকানা:** তুষভান্ডার, কালীগঞ্জ, লালমনিরহাট, রংপুর, বাংলাদেশ
- **YouTube:** https://youtube.com/@utpalmohontochoton
- **GitHub:** https://github.com/utpalmohonto078-ship-it

## V2 Features

- Bengali and English syntax
- Variables, expressions, conditions, loops and functions
- GLOBAL, BREAK and CONTINUE
- List and Dict collections, including nested collections
- Collection indexing, reading and assignment
- Static type checking and semantic validation
- Input builtin: Bengali নাও() and English input(), with optional prompt

## Runtime and Testing

Python VM is the executable V2 runtime. JavaScript and C++ currently provide semantic/type-checker validation only.

Latest verified V2 test suite: **171/171 PASS**.

See [docs/STATUS.md](docs/STATUS.md) for implementation status and [learning/README.md](learning/README.md) for learning materials.


<!-- BB-PACKAGE-SECTION-START -->
## Package Manager

Bangladesh Bhasha V2 supports local-directory package management.

Commands:

- `bhasha pkg init [name]` — create a project manifest.
- `bhasha pkg install <package-directory>` — install a local package.
- `bhasha pkg add <package-directory>` — install and record a dependency.
- `bhasha pkg remove <name>` — remove an installed package.
- `bhasha pkg list` — list installed packages.

Manifest: `bhasha-package.json`

Install location: `.bhasha/packages/`

Current limitations:
- Local directory packages only; no remote registry or publishing.
- No automatic dependency resolver or downloader.
- No language-runtime package import integration.
- Installed package source code is not automatically executed.
- This is not a complete security sandbox.

## Developer Tools

V2 includes the CLI, formatter, linter, validator, test runner, debugger, standard-library utilities and local Package Manager.
<!-- BB-PACKAGE-SECTION-END -->

## License

Proprietary Software — All Rights Reserved. See [LICENSE](LICENSE). Unauthorized copying, modification, redistribution, or commercial use is prohibited without prior written permission.
