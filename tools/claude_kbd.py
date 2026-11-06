#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["hidapi>=0.14"]
# ///
"""Send the Claude Code status to a keyboard running nice_view_lgtm + zmk-raw-hid.

    claude_kbd.py working|needs|idle   send that status now
    claude_kbd.py --from-state         send the status stored in the state file
    claude_kbd.py --probe              list matching raw HID devices and send "idle"

Claude Code hooks write the wanted status to STATE_FILE synchronously (so the order
of hooks is kept) and start `--from-state` in the background, which takes a lock
and sends whatever the file says *now*. A missing keyboard is never an error:
the script always exits 0 so it can't get in Claude Code's way.

Report: [report id 0] 'C' <status> padded to the 32 byte raw HID report.
"""

import fcntl
import sys
import time
from pathlib import Path

USAGE_PAGE = 0xFF60   # CONFIG_RAW_HID_USAGE_PAGE
USAGE = 0x61          # CONFIG_RAW_HID_USAGE
REPORT_SIZE = 32      # CONFIG_RAW_HID_REPORT_SIZE
STATUSES = {"idle": 0, "working": 1, "needs": 2}

STATE_DIR = Path.home() / ".claude" / "claude-kbd"
STATE_FILE = STATE_DIR / "state"
SENT_FILE = STATE_DIR / "sent"
LOCK_FILE = STATE_DIR / "lock"
RESEND_AFTER_S = 60   # resend an unchanged status now and then (keyboard may have rebooted)


def find_devices(hid):
    return [d for d in hid.enumerate()
            if d.get("usage_page") == USAGE_PAGE and d.get("usage") == USAGE]


def send(status):
    import hid  # imported late so --help works without the dependency

    report = bytes([0x00, ord("C"), STATUSES[status]]).ljust(REPORT_SIZE + 1, b"\x00")
    sent = 0
    for info in find_devices(hid):
        dev = hid.device()
        try:
            dev.open_path(info["path"])
            if dev.write(report) > 0:
                sent += 1
        except (OSError, ValueError):
            pass
        finally:
            dev.close()
    return sent


def send_from_state():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOCK_FILE, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        status = STATE_FILE.read_text().strip() if STATE_FILE.exists() else "idle"
        if status not in STATUSES:
            return
        last = SENT_FILE.read_text().split() if SENT_FILE.exists() else []
        if last and last[0] == status and time.time() - float(last[1]) < RESEND_AFTER_S:
            return
        if send(status):
            SENT_FILE.write_text(f"{status} {time.time()}")


def probe():
    import hid

    devices = find_devices(hid)
    if not devices:
        print(f"No HID device with usage page 0x{USAGE_PAGE:04X} / usage 0x{USAGE:02X} found.")
        print("Is the left half flashed with raw_hid_adapter and connected (USB or Bluetooth)?")
        return
    for d in devices:
        print(f"{d.get('manufacturer_string')} {d.get('product_string')} "
              f"vid=0x{d['vendor_id']:04X} pid=0x{d['product_id']:04X} path={d['path']!r}")
    print(f"sent 'idle' to {send('idle')} device(s)")


def forget_sent():
    """A manual send bypasses the state file; make the next hook send again."""
    SENT_FILE.unlink(missing_ok=True)


def main(argv):
    try:
        if argv == ["--probe"]:
            forget_sent()
            probe()
        elif argv == ["--from-state"]:
            send_from_state()
        elif len(argv) == 1 and argv[0] in STATUSES:
            forget_sent()
            print(f"sent '{argv[0]}' to {send(argv[0])} device(s)")
        else:
            print(__doc__)
    except Exception as err:  # never fail a Claude Code hook
        print(f"claude_kbd: {err}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
