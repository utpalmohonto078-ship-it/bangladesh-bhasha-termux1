# BANGLADESH BHASHA — Android

Android application for the original BANGLADESH BHASHA ULTIMATE project.

## Architecture

- Native Android Java Activity
- Chaquopy Python runtime
- Original `bb.py` compiler pipeline
- Original `compiler/` package
- Original `runtime/` package
- Offline source compilation and VM execution

## Build integration

The Gradle task `syncBhashaPython` copies the original compiler,
runtime and `bb.py` into the Android Python source directory
before Android preBuild.

The original source files remain in the project root.

## Current limitations

This is the first compiler/VM integration stage.
A successful APK build and on-device execution test are still required.

Universal Analyzer, scientific research engines, satellite data
connectors, medical research modules, materials science modules,
native runtime and other platform builds remain separate development
tasks. They are not claimed as completed.

The project retains its existing proprietary All Rights Reserved license.
