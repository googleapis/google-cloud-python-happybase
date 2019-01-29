# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Check if all public modules are included in our docs."""


from __future__ import print_function

import argparse
import os
import sys
import warnings

from sphinx.ext.intersphinx import fetch_inventory


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
IGNORED_PREFIXES = ("test_", "_")
IGNORED_MODULES = frozenset(["google.__init__", "google.cloud.__init__"])
PACKAGES = ("src",)


class SphinxApp(object):
    """Mock app to interact with Sphinx helpers."""

    warn = warnings.warn
    srcdir = DOCS_DIR


def is_valid_module(filename):
    """Determines if a filename is a valid Python module.

    Assumes if is just the end of a path (i.e. does not contain
    ``os.path.sep``.

    :type filename: string
    :param filename: The name of a file.

    :rtype: bool
    :returns: Flag indicating if the filename is valid.
    """
    if not filename.endswith(".py"):
        return False
    if filename == "__init__.py":
        return True
    for prefix in IGNORED_PREFIXES:
        if filename.startswith(prefix):
            return False
    return True


def get_public_modules(path, base_package=None):
    """Get list of all public modules relative to a path.

    :type path: string
    :param path: The path containing the python modules.

    :type base_package: string
    :param base_package: (Optional) A package to prepend in
                         front of the path.

    :rtype: list
    :returns: List of all modules found.
    """
    result = []
    for subdir, _, files in os.walk(path):
        # Skip folders that start with _.
        if any([part.startswith("_") for part in subdir.split(os.path.sep)]):
            continue
        _, rel_dir = subdir.split(path)
        rel_dir = rel_dir.lstrip(os.path.sep)
        for filename in files:
            if is_valid_module(filename):
                mod_name, _ = os.path.splitext(filename)
                rel_path = os.path.join(rel_dir, mod_name)
                if base_package is not None:
                    rel_path = os.path.join(base_package, rel_path)
                # Turn into a Python module rather than a file path.
                result.append(rel_path.replace(os.path.sep, "."))

    return result


def verify_modules(build_root="_build"):
    """Verify modules included.

    :type build_root: str
    :param build_root: The root of the directory where docs are built into.
                       Defaults to ``_build``.
    """
    object_inventory_relpath = os.path.join(build_root, "html", "objects.inv")

    mock_uri = ""
    inventory = fetch_inventory(SphinxApp, mock_uri, object_inventory_relpath)
    sphinx_mods = set(inventory["py:module"].keys())

    public_mods = set()
    for package in PACKAGES:
        library_dir = os.path.join(BASE_DIR, package, "google", "cloud")
        package_mods = get_public_modules(library_dir, base_package="google.cloud")
        public_mods.update(package_mods)

    if not sphinx_mods <= public_mods:
        unexpected_mods = sphinx_mods - public_mods
        message = [
            "Unexpected error. There were modules referenced by "
            "Sphinx that are not among the public modules."
        ]
        message.extend(["- %s" % (mod,) for mod in unexpected_mods])
        print("\n".join(message), file=sys.stderr)
        sys.exit(1)

    undocumented_mods = public_mods - sphinx_mods
    # Remove ignored modules.
    undocumented_mods -= IGNORED_MODULES
    if undocumented_mods:
        message_parts = ["Found undocumented public modules:"]
        message_parts.extend(
            ["- " + mod_name for mod_name in sorted(undocumented_mods)]
        )
        print("\n".join(message_parts), file=sys.stderr)
        sys.exit(1)


def get_parser():
    """Get simple ``argparse`` parser to determine package.

    :rtype: :class:`argparse.ArgumentParser`
    :returns: The parser for this script.
    """
    description = "Run check that all google-cloud " "modules are included in docs."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--build-root",
        dest="build_root",
        help="The root directory where docs are located.",
    )
    return parser


def main():
    """Main script to verify modules included."""
    parser = get_parser()
    args = parser.parse_args()
    verify_modules(build_root=args.build_root)


if __name__ == "__main__":
    main()
