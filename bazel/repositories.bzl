load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def ocv_repositories():
    http_archive(
        name = "qigao_opencv_source",
        urls = ["https://codeload.github.com/opencv/opencv/tar.gz/refs/tags/4.11.0"],
        type = "tar.gz",
        sha256 = "9a7c11f924eff5f8d8070e297b322ee68b9227e003fd600d4b8122198091665f",
        strip_prefix = "opencv-4.11.0",
        build_file_content = """
filegroup(name = "all", srcs = glob(["**"]), visibility = ["//visibility:public"])
""",
    )
