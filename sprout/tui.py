"""sprout TUI — simple curses interface."""

import curses

from sprout.diff import diff_system, format_diff
from sprout.packages import list_installed, search, install, remove


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(False)

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        stdscr.addstr(0, 0, " sprout tui ".center(w, "="))
        stdscr.addstr(1, 2, "[1] diff — show config changes")
        stdscr.addstr(2, 2, "[2] info — installed packages")
        stdscr.addstr(3, 2, "[3] search — search packages")
        stdscr.addstr(4, 2, "[4] install — install package")
        stdscr.addstr(5, 2, "[5] remove — remove package")
        stdscr.addstr(6, 2, "[q] quit")

        stdscr.addstr(h - 1, 0, " choose: ".center(w, "-"))
        stdscr.refresh()

        ch = stdscr.getch()

        if ch == ord("q"):
            break
        elif ch == ord("1"):
            _show_diff(stdscr)
        elif ch == ord("2"):
            _show_info(stdscr)
        elif ch == ord("3"):
            _show_search(stdscr)
        elif ch == ord("4"):
            _show_install(stdscr)
        elif ch == ord("5"):
            _show_remove(stdscr)


def _show_diff(stdscr):
    result = diff_system()
    output = format_diff(result)
    _show_pager(stdscr, "diff", output)


def _show_info(stdscr):
    pkgs = list_installed()
    lines = [f"  {len(pkgs)} installed packages:", ""]
    for p in pkgs:
        lines.append(f"    {p}")
    _show_pager(stdscr, "installed packages", "\n".join(lines))


def _show_search(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "search: ")
    stdscr.refresh()
    curses.echo()
    query = stdscr.getstr(0, 8, 40).decode()
    curses.noecho()

    if query:
        results = search(query)
        if results:
            lines = [f"  results for '{query}':", ""]
            for p in results[:50]:
                lines.append(f"    {p}")
        else:
            lines = [f"  no results for '{query}'"]
        _show_pager(stdscr, "search", "\n".join(lines))


def _show_install(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "install: ")
    stdscr.refresh()
    curses.echo()
    pkg = stdscr.getstr(0, 9, 40).decode()
    curses.noecho()

    if pkg:
        try:
            install(pkg)
            _show_pager(stdscr, "install", f"  installed: {pkg}")
        except Exception as e:
            _show_pager(stdscr, "install", f"  failed: {e}")


def _show_remove(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "remove: ")
    stdscr.refresh()
    curses.echo()
    pkg = stdscr.getstr(0, 8, 40).decode()
    curses.noecho()

    if pkg:
        try:
            remove(pkg)
            _show_pager(stdscr, "remove", f"  removed: {pkg}")
        except Exception as e:
            _show_pager(stdscr, "remove", f"  failed: {e}")


def _show_pager(stdscr, title, text):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    stdscr.addstr(0, 0, f" {title} ".center(w, "="))

    lines = text.split("\n")
    y = 1
    for line in lines:
        if y >= h - 2:
            break
        stdscr.addstr(y, 0, line[:w - 1])
        y += 1

    stdscr.addstr(h - 1, 0, " press any key ".center(w, "-"))
    stdscr.refresh()
    stdscr.getch()


def run():
    curses.wrapper(main)
