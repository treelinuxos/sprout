# Sprout Package Manager

Sprout is a declarative package manager for Alpine Linux. It uses `.prc` (Treelinux Config) files to define the desired state of the system.

## Core Concepts

- **Declarative**: You declare what you want, sprout makes it happen
- **Atomic**: Changes are applied atomically with automatic backups
- **Modular**: Supports `.smp` modules for custom logic at apply time

## .prc Config Format

```
# comments start with #
block_name
	item1
	item2
	key value

include other.prc
```

### Block Types

- `packages` - list of packages to install
- `services` - list of services to enable (with `enable ` prefix)
- `modules` - list of `.smp` modules to run at apply time
- `user` - user configuration (dict with `name`, `shell`, etc.)
- `dotfiles` - list of dotfiles to manage

### Example

```
packages
	neovim
	firefox
	git

services
	sshd
	enable networking

modules
	update-sprout.smp
	nvidia.smp

include desktop.prc
```

## Commands

- `sprout apply` - apply system.prc to live system
- `sprout apply --non-interactive` - apply without prompts
- `sprout diff` - show differences between config and system
- `sprout status` - show system status
- `sprout backup list` - list available backups
- `sprout backup rollback` - rollback to previous state
- `sprout search <query>` - search for packages
- `sprout install <pkg>` - install a package
- `sprout remove <pkg>` - remove a package

## .smp Modules

`.smp` (Sprout Module Packages) are Python scripts that run at apply time. They have access to the `sprout_lib` library for system interaction.

### Module Example

```python
#!/usr/bin/env python3
import sprout_lib

sprout_lib.info("Configuring nvidia drivers...")
# custom logic here
sprout_lib.info("Done!")
```

### sprout_lib API

- `info(msg)` - log info message
- `warn(msg)` - log warning message
- `error(msg)` - log error message
- `run(cmd)` - run a system command
- `file_write(path, content)` - write file
- `file_read(path)` - read file
- `package_install(pkg)` - install package
- `service_enable(svc)` - enable service

## Installation

```bash
pip install sprout
```

Or from source:

```bash
git clone https://github.com/treelinuxos/sprout.git
cd sprout
pip install -e .
```

## License

gpl v3
