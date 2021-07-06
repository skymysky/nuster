# Copyright 2019 Ilya Shipitsin <chipitsine@gmail.com>
# Copyright 2020 Tim Duesterhus <tim@bastelstu.be>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version
# 2 of the License, or (at your option) any later version.

import json
import sys

if len(sys.argv) == 2:
    build_type = sys.argv[1]
else:
    print("Usage: {} <build_type>".format(sys.argv[0]), file=sys.stderr)
    sys.exit(1)

print("Generating matrix for type '{}'.".format(build_type))


def clean_os(os):
    if os == "ubuntu-latest":
        return "Ubuntu"
    elif os == "macos-latest":
        return "macOS"
    return os.replace("-latest", "")


def clean_ssl(ssl):
    return ssl.replace("_VERSION", "").lower()


def clean_compression(compression):
    return compression.replace("USE_", "").lower()


def get_asan_flags(cc):
    if cc == "clang":
        return [
            "USE_OBSOLETE_LINKER=1",
            'DEBUG_CFLAGS="-g -fsanitize=address"',
            'LDFLAGS="-fsanitize=address"',
            'CPU_CFLAGS.generic="-O1"',
        ]

    raise ValueError("ASAN is only supported for clang")


matrix = []

# Ubuntu

os = "ubuntu-latest"
TARGET = "linux-glibc"
for CC in ["gcc", "clang"]:
    matrix.append(
        {
            "name": "{}, {}, no features".format(clean_os(os), CC),
            "os": os,
            "TARGET": TARGET,
            "CC": CC,
            "FLAGS": [],
        }
    )

    matrix.append(
        {
            "name": "{}, {}, all features".format(clean_os(os), CC),
            "os": os,
            "TARGET": TARGET,
            "CC": CC,
            "FLAGS": [
                "USE_ZLIB=1",
                "USE_PCRE=1",
                "USE_PCRE_JIT=1",
                "USE_LUA=1",
                "USE_OPENSSL=1",
                "USE_SYSTEMD=1",
                "USE_WURFL=1",
                "WURFL_INC=contrib/wurfl",
                "WURFL_LIB=contrib/wurfl",
                "USE_DEVICEATLAS=1",
                "DEVICEATLAS_SRC=contrib/deviceatlas",
                "EXTRA_OBJS=contrib/prometheus-exporter/service-prometheus.o",
                "USE_51DEGREES=1",
                "51DEGREES_SRC=contrib/51d/src/pattern",
            ],
        }
    )

    for compression in ["USE_SLZ=1", "USE_ZLIB=1"]:
        matrix.append(
            {
                "name": "{}, {}, gz={}".format(
                    clean_os(os), CC, clean_compression(compression)
                ),
                "os": os,
                "TARGET": TARGET,
                "CC": CC,
                "FLAGS": [compression],
            }
        )

    for ssl in [
        "stock",
        "OPENSSL_VERSION=1.0.2u",
        "LIBRESSL_VERSION=2.9.2",
        "LIBRESSL_VERSION=3.3.0",
        "BORINGSSL=yes",
    ]:
        flags = ["USE_OPENSSL=1"]
        if ssl != "stock":
            flags.append("SSL_LIB=${HOME}/opt/lib")
            flags.append("SSL_INC=${HOME}/opt/include")
        matrix.append(
            {
                "name": "{}, {}, ssl={}".format(clean_os(os), CC, clean_ssl(ssl)),
                "os": os,
                "TARGET": TARGET,
                "CC": CC,
                "ssl": ssl,
                "FLAGS": flags,
            }
        )

# ASAN

os = "ubuntu-latest"
CC = "clang"
TARGET = "linux-glibc"
matrix.append(
    {
        "name": "{}, {}, ASAN, all features".format(clean_os(os), CC),
        "os": os,
        "TARGET": TARGET,
        "CC": CC,
        "FLAGS": get_asan_flags(CC)
        + [
            "USE_ZLIB=1",
            "USE_PCRE=1",
            "USE_PCRE_JIT=1",
            "USE_LUA=1",
            "USE_OPENSSL=1",
            "USE_SYSTEMD=1",
            "USE_WURFL=1",
            "WURFL_INC=contrib/wurfl",
            "WURFL_LIB=contrib/wurfl",
            "USE_DEVICEATLAS=1",
            "DEVICEATLAS_SRC=contrib/deviceatlas",
            "EXTRA_OBJS=contrib/prometheus-exporter/service-prometheus.o",
            "USE_51DEGREES=1",
            "51DEGREES_SRC=contrib/51d/src/pattern",
        ],
    }
)

# macOS

os = "macos-latest"
TARGET = "osx"
for CC in ["clang"]:
    matrix.append(
        {
            "name": "{}, {}, no features".format(clean_os(os), CC),
            "os": os,
            "TARGET": TARGET,
            "CC": CC,
            "FLAGS": [],
        }
    )

# Print matrix

print(json.dumps(matrix, indent=4, sort_keys=True))

print("::set-output name=matrix::{}".format(json.dumps({"include": matrix})))
