"""
.smp module runner — execute MicroPython module scripts.

runs .smp files and provides the sprout library for hardware detection,
package application, and system interaction.
"""

import os
import sys
import subprocess


class ModuleError(Exception):
    """raised when a module fails to run."""
    pass


def run_module(script_path, module_dir=None):
    """run a .smp module script.

    script_path: path to the .smp file.
    module_dir: directory with the sprout MicroPython library.
    """
    if not os.path.isfile(script_path):
        print(f"! module not found: {script_path}")
        sys.exit(1)

    if not script_path.endswith(".smp"):
        print(f"! not a .smp file: {script_path}")
        sys.exit(1)

    # find micropython
    micropython = _find_micropython()
    if micropython is None:
        print("! micropython not found")
        print("  install with: apk add micropython")
        sys.exit(1)

    # set up module search path
    if module_dir is None:
        module_dir = "/usr/lib/sprout"

    env = os.environ.copy()
    env["MICROPYPATH"] = module_dir

    print(f"  running: {os.path.basename(script_path)}")

    try:
        result = subprocess.run(
            [micropython, script_path],
            env=env,
            timeout=300,
        )
        if result.returncode != 0:
            raise ModuleError(
                f"module failed with exit code {result.returncode}"
            )
    except subprocess.TimeoutExpired:
        raise ModuleError("module timed out after 5 minutes")


def _find_micropython():
    """find the micropython binary."""
    for path in ["/usr/bin/micropython", "/usr/local/bin/micropython"]:
        if os.path.isfile(path):
            return path

    # try in PATH
    for d in os.environ.get("PATH", "").split(":"):
        candidate = os.path.join(d, "micropython")
        if os.path.isfile(candidate):
            return candidate

    return None
