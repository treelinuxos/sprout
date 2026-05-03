"""
sprout — MicroPython library for .smp modules.

this is the library that .smp scripts import to interact with the system.
it provides hardware detection, package application, and privilege handling.

example usage:
    import sprout_micro

    gpu = sprout.detect("gpu")
    if gpu == "nvidia":
        sprout.apply("nvidia-drivers")
    sprout.apply("steam")
"""

import os
import sys
import subprocess


def apply(package_or_packages):
    """install a package (or list of packages).

    uses doas if not running as root.
    """
    if isinstance(package_or_packages, str):
        packages = [package_or_packages]
    else:
        packages = list(package_or_packages)

    print(f"  sprout.apply: {', '.join(packages)}")

    cmd = ["apk", "add"] + packages
    if os.geteuid() != 0:
        cmd = ["doas"] + cmd

    result = subprocess.run(cmd, timeout=300)
    if result.returncode != 0:
        print(f"! failed to install: {', '.join(packages)}")
        sys.exit(1)


def remove(package_or_packages):
    """remove a package (or list of packages)."""
    if isinstance(package_or_packages, str):
        packages = [package_or_packages]
    else:
        packages = list(package_or_packages)

    print(f"  sprout.remove: {', '.join(packages)}")

    cmd = ["apk", "del", "--purge"] + packages
    if os.geteuid() != 0:
        cmd = ["doas"] + cmd

    result = subprocess.run(cmd, timeout=300)
    if result.returncode != 0:
        print(f"! failed to remove: {', '.join(packages)}")
        sys.exit(1)


def detect(hardware_type):
    """detect hardware information.

    hardware_type: "gpu", "cpu", "network", "storage", etc.
    returns a string identifier or None.
    """
    if hardware_type == "gpu":
        return _detect_gpu()
    elif hardware_type == "cpu":
        return _detect_cpu()
    elif hardware_type == "network":
        return _detect_network()
    else:
        return None


def _detect_gpu():
    """detect the GPU vendor."""
    try:
        result = subprocess.run(
            ["lspci"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout.lower()
        if "nvidia" in output:
            return "nvidia"
        elif "amd" in output or "ati" in output or "radeon" in output:
            return "amd"
        elif "intel" in output:
            return "intel"
    except Exception:
        pass

    # fallback: check /sys
    try:
        if os.path.isdir("/sys/class/drm"):
            for entry in os.listdir("/sys/class/drm"):
                if "nvidia" in entry.lower():
                    return "nvidia"
                if "radeon" in entry.lower():
                    return "amd"
    except Exception:
        pass

    return None


def _detect_cpu():
    """detect the CPU architecture."""
    import platform
    machine = platform.machine()
    if machine in ("x86_64", "AMD64"):
        return "x86_64"
    elif machine in ("aarch64", "arm64"):
        return "aarch64"
    elif machine.startswith("arm"):
        return "arm"
    return machine


def _detect_network():
    """detect the primary network interface type."""
    try:
        result = subprocess.run(
            ["lspci"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout.lower()
        if "wireless" in output or "wi-fi" in output or "802.11" in output:
            return "wifi"
    except Exception:
        pass
    return "ethernet"


def service_enable(name):
    """enable and start a runit service."""
    print(f"  sprout.service_enable: {name}")
    sv_dir = f"/etc/runit/runsvdir/default/{name}"
    svc_dir = f"/etc/sv/{name}"

    if not os.path.isdir(svc_dir):
        print(f"! service not found: {name}")
        return False

    if os.geteuid() != 0:
        subprocess.run(["doas", "ln", "-sf", svc_dir, sv_dir])
    else:
        os.symlink(svc_dir, sv_dir)

    return True


def service_disable(name):
    """disable a runit service."""
    print(f"  sprout.service_disable: {name}")
    sv_dir = f"/etc/runit/runsvdir/default/{name}"
    if os.path.islink(sv_dir):
        if os.geteuid() != 0:
            subprocess.run(["doas", "rm", "-f", sv_dir])
        else:
            os.unlink(sv_dir)
    return True


def is_installed(package):
    """check if a package is installed."""
    result = subprocess.run(
        ["apk", "list", "--installed", package],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode == 0


def info(message):
    """print an info message from the module."""
    print(f"  [module] {message}")


def warn(message):
    """print a warning message from the module."""
    print(f"  [module] ! {message}")
