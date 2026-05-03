"""
doas integration — privilege escalation for sprout.

sprout uses doas internally so users don't need to prefix commands manually.
when a privileged operation is needed, sprout prompts for the password and
handles escalation.
"""

import os
import subprocess
import sys

DOAS_CONFIG = "/etc/doas.d/sprout.conf"


class PrivilegeError(Exception):
    """raised when privilege escalation fails."""
    pass


def is_root():
    """check if running as root."""
    return os.geteuid() == 0


def require_root(operation):
    """exit with error if not root."""
    if not is_root():
        print(f"! {operation} requires root privileges", file=sys.stderr)
        print(f"  run with: doas sprout ...", file=sys.stderr)
        sys.exit(1)


def doas(*args, stdin_data=None):
    """run a command with doas privilege escalation.

    prompts for password if needed.
    returns (stdout, stderr, returncode).
    """
    cmd = ["doas"] + list(args)
    try:
        result = subprocess.run(
            cmd,
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        raise PrivilegeError("doas not found — install it with: apk add opendoas")
    except subprocess.TimeoutExpired:
        raise PrivilegeError("command timed out")


def doas_run(*args):
    """run a command with doas, streaming output to the terminal.

    this is for commands that need interactive input (like password prompts).
    returns the return code.
    """
    cmd = ["doas"] + list(args)
    try:
        result = subprocess.run(cmd, timeout=300)
        return result.returncode
    except FileNotFoundError:
        raise PrivilegeError("doas not found — install it with: apk add opendoas")
    except subprocess.TimeoutExpired:
        raise PrivilegeError("command timed out")


def configure_doas():
    """write the sprout doas config to allow password-authenticated root.

    creates /etc/doas.d/sprout.conf:
        permit :wheel
        permit nopass root
    """
    require_root("configure doas")

    config = (
        "# sprout doas configuration\n"
        "permit :wheel\n"
        "permit nopass root\n"
    )

    os.makedirs(os.path.dirname(DOAS_CONFIG), exist_ok=True)
    with open(DOAS_CONFIG, "w") as f:
        f.write(config)

    os.chmod(DOAS_CONFIG, 0o644)
    print(f"  doas configured at {DOAS_CONFIG}")


def run_with_privilege(cmd, operation="operation"):
    """run a command, escalating privileges if needed.

    if already root, runs directly.
    otherwise, tries doas.

    cmd: list of command arguments.
    operation: description for error messages.
    returns the return code.
    """
    if is_root():
        try:
            result = subprocess.run(cmd, timeout=300)
            return result.returncode
        except subprocess.TimeoutExpired:
            print(f"! {operation} timed out", file=sys.stderr)
            return 1

    # not root — try doas
    doas_cmd = ["doas"] + cmd
    try:
        result = subprocess.run(doas_cmd, timeout=300)
        if result.returncode != 0:
            print(f"! {operation} failed", file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print(f"! doas not found — install with: apk add opendoas", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print(f"! {operation} timed out", file=sys.stderr)
        return 1
