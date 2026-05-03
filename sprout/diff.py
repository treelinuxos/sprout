"""
diff engine — compare desired config vs actual system state.

compares what system.prc says should be installed with what is actually
installed, and what services should be enabled vs what is running.
"""

from sprout.parser import parse, resolve_includes
from sprout import packages
from sprout import utils


class SystemState:
    """snapshot of the current system state."""

    def __init__(self):
        self.installed_packages = set()
        self.enabled_services = set()
        self.config_files = {}

    def refresh(self):
        """refresh all state from the live system."""
        self.installed_packages = set(packages.list_installed())


def diff_config(config_path, system_state=None):
    """diff a config file against the live system.

    returns a dict:
        {
            "packages": {
                "to_install": [...],
                "to_remove": [...],
            },
            "services": {
                "to_enable": [...],
                "to_disable": [...],
            },
        }
    """
    if system_state is None:
        system_state = SystemState()
        system_state.refresh()

    config = parse(config_path)
    config = resolve_includes(config, config_path)

    result = {
        "packages": {"to_install": [], "to_remove": []},
        "services": {"to_enable": [], "to_disable": []},
        "users": {},
        "includes": config["includes"],
    }

    blocks = config["blocks"]

    # diff packages
    desired_packages = set(blocks.get("packages", []))
    for pkg in desired_packages:
        if pkg not in system_state.installed_packages:
            result["packages"]["to_install"].append(pkg)

    for pkg in system_state.installed_packages:
        if pkg not in desired_packages:
            result["packages"]["to_remove"].append(pkg)

    # diff services
    desired_services = set()
    for entry in blocks.get("services", []):
        if entry.startswith("enable "):
            desired_services.add(entry[7:].strip())

    enabled_services = _get_enabled_services()
    for svc in desired_services:
        if svc not in enabled_services:
            result["services"]["to_enable"].append(svc)

    for svc in enabled_services:
        if svc not in desired_services:
            result["services"]["to_disable"].append(svc)

    # user block info
    if "user" in blocks and isinstance(blocks["user"], dict):
        result["users"]["desired"] = blocks["user"]

    return result


def diff_system():
    """diff system.prc + all user configs against the live system.

    returns a combined diff dict.
    """
    system_state = SystemState()
    system_state.refresh()

    result = {
        "system": {},
        "users": {},
    }

    if utils.is_root() or True:  # diff works without root
        if __import__("os").path.isfile(utils.SYSTEM_CONFIG):
            result["system"] = diff_config(
                utils.SYSTEM_CONFIG, system_state
            )
        else:
            result["system"] = {
                "error": f"no config at {utils.SYSTEM_CONFIG}",
                "packages": {"to_install": [], "to_remove": []},
                "services": {"to_enable": [], "to_disable": []},
            }

        # diff user configs
        if __import__("os").path.isdir(utils.USER_CONFIG_DIR):
            for f in __import__("os").listdir(utils.USER_CONFIG_DIR):
                if f.endswith(".prc"):
                    username = f[:-4]
                    path = __import__("os").path.join(
                        utils.USER_CONFIG_DIR, f
                    )
                    result["users"][username] = diff_config(
                        path, system_state
                    )

    return result


def format_diff(diff):
    """format a diff dict for human-readable output."""
    lines = []

    if isinstance(diff.get("system"), dict):
        sys_diff = diff["system"]
        if "error" in sys_diff:
            lines.append(f"! {sys_diff['error']}")
            lines.append("")

        pkgs = sys_diff.get("packages", {})
        svcs = sys_diff.get("services", {})

        to_install = pkgs.get("to_install", [])
        to_remove = pkgs.get("to_remove", [])
        to_enable = svcs.get("to_enable", [])
        to_disable = svcs.get("to_disable", [])

        if to_install:
            lines.append("packages to install:")
            for p in to_install:
                lines.append(f"  + {p}")
            lines.append("")

        if to_remove:
            lines.append("packages not in system.prc:")
            for p in to_remove:
                lines.append(f"  - {p}")
            lines.append("")

        if to_enable:
            lines.append("services to enable:")
            for s in to_enable:
                lines.append(f"  + {s}")
            lines.append("")

        if to_disable:
            lines.append("services not in system.prc:")
            for s in to_disable:
                lines.append(f"  - {s}")
            lines.append("")

    if diff.get("users"):
        for username, user_diff in diff["users"].items():
            lines.append(f"user: {username}")
            pkgs = user_diff.get("packages", {})
            to_install = pkgs.get("to_install", [])
            to_remove = pkgs.get("to_remove", [])

            if to_install:
                for p in to_install:
                    lines.append(f"  + {p}")
            if to_remove:
                for p in to_remove:
                    lines.append(f"  - {p}")
            lines.append("")

    if len(lines) == 0:
        return "  system is in sync with config\n"

    return "\n".join(lines)


def _get_enabled_services():
    """get set of currently enabled/running services.

    on a runit system, services are enabled by having a symlink in
    /etc/runit/runsvdir/default/ pointing to the service dir.
    """
    import os
    runit_dir = "/etc/runit/runsvdir/default"
    if not os.path.isdir(runit_dir):
        return set()

    enabled = set()
    for entry in os.listdir(runit_dir):
        if os.path.islink(os.path.join(runit_dir, entry)):
            enabled.add(entry)
    return enabled
