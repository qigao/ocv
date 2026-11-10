#!/usr/bin/env python3
"""Build and package a pinned OpenCV SDK."""

import argparse
import hashlib
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VERSION = "4.11.0"
SOURCE_SHA = {
    "opencv": "9a7c11f924eff5f8d8070e297b322ee68b9227e003fd600d4b8122198091665f",
    "opencv_contrib": "2dfc5957201de2aa785064711125af6abb2e80a64e2dc246aca4119b19687041",
}
FFMPEG_URL = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/d63d7c154c57242bf2283be61166be2bd30ec47e/ffmpeg"
FFMPEG = {
    "opencv_videoio_ffmpeg.dll": (
        "642b94d032a8292b07550126934173f6",
        "ba75417eeaf2c5767ed9fad80fe3ede55a3fe67493218d6074d21c7732e03d78",
    ),
    "opencv_videoio_ffmpeg_64.dll": (
        "a8c3560c8f20e1ae465bef81580fa92c",
        "f0460320ac08c074bdf6d5a19f5c13d204e585e85030fdd40e20a3c0b3adeb67",
    ),
    "ffmpeg_version.cmake": (
        "8862c87496e2e8c375965e1277dee1c7",
        "94d8bef0d4441f4dc4198f55278ae42cda5da762c9991daf83be76167d82c447",
    ),
}


def verify(path, expected):
    with path.open("rb") as source:
        if hashlib.file_digest(source, "sha256").hexdigest() != expected:
            raise ValueError(f"SHA-256 mismatch for {path}")


def download(url, path, sha256):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        partial = path.with_name(path.name + ".part")
        subprocess.run(["curl", "-fsSL", "--retry", "3", url, "-o", partial], check=True)
        verify(partial, sha256)
        partial.replace(path)
    verify(path, sha256)


def extract_source(out, name):
    archive = out / "downloads" / f"{name}-{VERSION}.tar.gz"
    url = f"https://codeload.github.com/opencv/{name}/tar.gz/refs/tags/{VERSION}"
    download(url, archive, SOURCE_SHA[name])
    source = out / "sources" / name
    source.mkdir(parents=True, exist_ok=True)
    subprocess.run(["tar", "-xzf", archive, "--strip-components=1", "-C", source], check=True)
    return source


def configuration(args, out):
    flags = [
        "-DENABLE_CCACHE=OFF",
        f"-DOPENCV_DOWNLOAD_PATH={out / 'downloads'}",
    ]
    if args.ccache:
        flags += ["-DCMAKE_C_COMPILER_LAUNCHER=ccache", "-DCMAKE_CXX_COMPILER_LAUNCHER=ccache"]
    if args.platform.startswith("android-"):
        abi = {"android-arm64": "arm64-v8a", "android-x64": "x86_64"}[args.platform]
        toolchain = Path(os.environ["ANDROID_NDK_HOME"]) / "build/cmake/android.toolchain.cmake"
        flags += [f"-DCMAKE_TOOLCHAIN_FILE={toolchain.resolve()}", f"-DANDROID_ABI={abi}", "-DANDROID_PLATFORM=android-26"]
    elif args.toolchain:
        flags.append(f"-DCMAKE_TOOLCHAIN_FILE={args.toolchain.resolve()}")

    if args.profile == "static":
        return ["-C", REPO / "bazel/static-profile.cmake", *flags]
    contrib = extract_source(out, "opencv_contrib")
    if args.platform == "windows-x64":
        for name, (md5, sha256) in FFMPEG.items():
            download(f"{FFMPEG_URL}/{name}", out / "downloads/ffmpeg" / f"{md5}-{name}", sha256)
    return flags + [
        "-DBUILD_TESTS=OFF",
        "-DBUILD_PERF_TESTS=OFF",
        "-DBUILD_EXAMPLES=OFF",
        "-DBUILD_JAVA=OFF",
        "-DBUILD_opencv_world=ON",
        "-DBUILD_SHARED_LIBS=ON",
        "-DWITH_FFMPEG=ON",
        "-DWITH_TBB=ON",
        "-DWITH_OPENMP=ON",
        f"-DOPENCV_EXTRA_MODULES_PATH={contrib / 'modules'}",
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform")
    parser.add_argument("--profile", choices=["static", "world"], default="static")
    parser.add_argument("--out", type=Path, default=Path("build-opencv"))
    parser.add_argument("--toolchain", type=Path)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--ccache", action="store_true")
    args = parser.parse_args()

    out = args.out.resolve()
    source = extract_source(out, "opencv")
    flags = configuration(args, out)
    install = out / "install" / f"{args.profile}-{args.platform}"
    configs = ["Debug", "Release"] if args.profile == "world" else ["Release"]
    for config in configs:
        build = out / "build" / f"{args.profile}-{args.platform}-{config}"
        prefix = install / config if args.profile == "world" else install
        subprocess.run([
            "cmake", "-S", source, "-B", build, "-G", "Ninja", *flags,
            f"-DCMAKE_BUILD_TYPE={config}", f"-DCMAKE_INSTALL_PREFIX={prefix}",
        ], check=True)
        subprocess.run(["cmake", "--build", build, "--parallel", str(args.jobs)], check=True)
        subprocess.run(["cmake", "--install", build], check=True)

    artifact = out / f"opencv-{VERSION}-{args.profile}-{args.platform}.tar.gz"
    subprocess.run(["tar", "-czf", artifact, "-C", install, "."], check=True)
    print(artifact)


if __name__ == "__main__":
    main()
