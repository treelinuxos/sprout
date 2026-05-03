# sprout

the treelinux package and configuration manager.

prototype in python 3. final version rewritten in go.

## commands

```
sprout install <pkg>     install a package
sprout remove <pkg>      remove a package
sprout upgrade <pkg>     upgrade a package
sprout update            safe update all
sprout update --force    full update
sprout apply             apply system.prc
sprout diff              preview changes
sprout search <query>    search packages
sprout run <script.smp>  run a module script
sprout info [pkg]        show installed packages
sprout rollback           restore from backup
sprout user              manage user configs
sprout --tui             launch tui
sprout --help            show help
```

## structure

```
sprout/
├── sprout/           — core library
│   ├── __main__.py   — entry point
│   ├── cli.py        — cli commands
│   ├── parser.py     — .prc parser
│   ├── packages.py   — apk wrapper
│   ├── backup.py     — config backup/rollback
│   ├── diff.py       — config vs system diff
│   ├── applier.py    — apply command
│   ├── privilege.py  — doas integration
│   ├── users.py      — per-user configs
│   ├── runner.py     — .smp module runner
│   └── tui.py        — curses tui
├── lib/sprout/       — micropython library for .smp modules
├── service/sprout/   — runit boot service
├── tests/            — test suite
├── examples/         — example .prc configs
└── modules/          — sample .smp modules
```

## quick start

```bash
python -m sprout --help
python -m sprout --tui
```

## license

gpl v3
