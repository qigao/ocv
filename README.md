# OCV

The desktop workflows build OpenCV World with FFmpeg for Linux and Windows.

The Bazel profile in `bazel/` builds the OpenCV 4.11.0 `core` and `imgproc` static libraries for GDMP. It uses the consuming build's C++ toolchain and disables optional desktop dependencies.

Register this repository as `qigao_ocv` in the consuming workspace and load its OpenCV source dependency.

```starlark
load("@qigao_ocv//bazel:repositories.bzl", "ocv_repositories")

ocv_repositories()
```

Link `@qigao_ocv//bazel:opencv` from your Bazel target. The consuming workspace supplies `rules_foreign_cc`. For Emscripten builds, pass `--define=ocv_wasm=1` with the Web toolchain flags.
