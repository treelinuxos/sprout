"""
doas integration — privilege escalation for sprout.

provides doas wrappers so sprout can escalate without requiring
the user to prefix every command.
"""

import subprocess
import sys


class PrivilegeError(Exception):
    """raised when privilege escalation fails."""
    pass


def doas(*args, stdin_data=None):
    """run a command with doas, capture output.

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
