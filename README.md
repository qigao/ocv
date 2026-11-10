# OCV

OpenCV CI builds the static `core` and `imgproc` SDK for Linux, macOS, Windows, and Android on x64 and ARM64. It uses the vcpkg-cache compiler and ccache setup, Apple Clang on macOS, and the NDK toolchain on Android.

Run the workflow with `profile=world` to build OpenCV World with FFmpeg and contrib modules for Linux or Windows x64. The World archives contain separate `Debug/` and `Release/` SDKs. Windows SDKs use LLVM-MinGW.

The Bazel profile in `bazel/` builds the OpenCV 4.11.0 `core` and `imgproc` static libraries for GDMP. Bazel and the native CI use the same [static CMake profile](bazel/static-profile.cmake).

Register this repository as `qigao_ocv` in the consuming workspace and load its OpenCV source dependency.

```starlark
load("@qigao_ocv//bazel:repositories.bzl", "ocv_repositories")

ocv_repositories()
```

Link `@qigao_ocv//bazel:opencv` from your Bazel target. The consuming workspace supplies `rules_foreign_cc`. For Emscripten builds, pass `--define=ocv_wasm=1` with the Web toolchain flags.
