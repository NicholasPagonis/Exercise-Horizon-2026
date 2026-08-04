#!/usr/bin/env python3
"""Build the Exercise Horizon 2026 site from event.json.

Generates:
  files/exercise-horizon-2026.ics   the calendar file participants download
  index.html                        the landing page, from templates/index.html

Everything volatile (date, location, contact, download list and file sizes)
lives in event.json so it is stated once. Prose lives in the template.

    python3 scripts/build.py

Stdlib only, no dependencies.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "event.json"
TEMPLATE = ROOT / "templates" / "index.html"
PAGE_OUT = ROOT / "index.html"
ICS_OUT = ROOT / "files" / "exercise-horizon-2026.ics"

PRODID = "-//Perth Airport//Exercise Horizon 2026//EN"


# --------------------------------------------------------------------------
# iCalendar
# --------------------------------------------------------------------------

def ics_escape(value: str) -> str:
    """Escape a TEXT value per RFC 5545 section 3.3.11."""
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def ics_param(value: str) -> str:
    """Quote a parameter value per RFC 5545 section 3.1.

    Parameter values use DQUOTE quoting, not the backslash escaping that TEXT
    values use. DQUOTE itself cannot appear in a quoted value, so drop it.
    """
    value = value.replace('"', "")
    return f'"{value}"' if any(c in value for c in ',;:') else value


def fold(line: str) -> list[str]:
    """Fold a content line to 75 octets, never splitting a UTF-8 sequence."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return [line]

    out, start = [], 0
    limit = 75
    while start < len(raw):
        end = min(start + limit, len(raw))
        # Back off until `end` sits on a character boundary (continuation
        # bytes match 0b10xxxxxx).
        while end > start and end < len(raw) and (raw[end] & 0xC0) == 0x80:
            end -= 1
        chunk = raw[start:end].decode("utf-8")
        out.append(chunk if start == 0 else " " + chunk)
        start = end
        limit = 74  # subsequent lines carry a leading space
    return out


def vtimezone(tzid: str) -> list[str]:
    """A minimal VTIMEZONE. Australia/Perth has had no DST since 2009."""
    if tzid != "Australia/Perth":
        raise SystemExit(
            f"error: no VTIMEZONE definition for {tzid!r}. Add one in "
            "scripts/build.py, or set event.all_day to true."
        )
    return [
        "BEGIN:VTIMEZONE",
        f"TZID:{tzid}",
        f"X-LIC-LOCATION:{tzid}",
        "BEGIN:STANDARD",
        "TZOFFSETFROM:+0800",
        "TZOFFSETTO:+0800",
        "TZNAME:AWST",
        "DTSTART:19700101T000000",
        "END:STANDARD",
        "END:VTIMEZONE",
    ]


def build_ics(ev: dict, contact: dict, site: dict, stamp: dt.datetime) -> str:
    date = dt.date.fromisoformat(ev["date"])
    all_day = bool(ev["all_day"])
    tzid = ev["timezone"]

    # The calendar entry may carry a status prefix the web page should not,
    # e.g. "[AWAITING EXTRA INFO] ...", so SUMMARY is overridable.
    summary = ev.get("ics_summary") or ev["name"]
    utc = stamp.strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{ics_escape(ev['name'])}",
        f"X-WR-TIMEZONE:{tzid}",
    ]

    if not all_day:
        lines += vtimezone(tzid)

    lines += [
        "BEGIN:VEVENT",
        f"UID:{ev['uid']}",
        f"DTSTAMP:{utc}",
        f"CREATED:{utc}",
        f"LAST-MODIFIED:{utc}",
        f"SEQUENCE:{int(ev['sequence'])}",
    ]

    if all_day:
        # DTEND is exclusive: a one-day event ends on the following date.
        lines += [
            f"DTSTART;VALUE=DATE:{date.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{(date + dt.timedelta(days=1)).strftime('%Y%m%d')}",
            "X-MICROSOFT-CDO-ALLDAYEVENT:TRUE",
        ]
    else:
        start = dt.time.fromisoformat(ev["start"])
        end = dt.time.fromisoformat(ev["end"])
        if end <= start:
            raise SystemExit("error: event.end must be later than event.start")
        fmt = "%Y%m%dT%H%M%S"
        lines += [
            f"DTSTART;TZID={tzid}:{dt.datetime.combine(date, start).strftime(fmt)}",
            f"DTEND;TZID={tzid}:{dt.datetime.combine(date, end).strftime(fmt)}",
        ]

    busy = bool(ev.get("busy", False))
    organizer_cn = contact.get("organizer_cn") or contact["team"]
    lines += [
        f"SUMMARY:{ics_escape(summary)}",
        f"LOCATION:{ics_escape(ev['location'])}",
        f"DESCRIPTION:{ics_escape(chr(10).join(ev['description']))}",
        f"URL:{site['base_url']}",
        f"STATUS:{ev['status']}",
        f"TRANSP:{'OPAQUE' if busy else 'TRANSPARENT'}",
        f"X-MICROSOFT-CDO-BUSYSTATUS:{'BUSY' if busy else 'FREE'}",
        "CLASS:PUBLIC",
        (
            f"ORGANIZER;CN={ics_param(organizer_cn)}:"
            f"mailto:{contact['email']}"
        ),
    ]

    if ev.get("categories"):
        lines.append(
            "CATEGORIES:" + ",".join(ics_escape(c) for c in ev["categories"])
        )

    for reminder in ev.get("reminders", []):
        # Accept a bare trigger string or {"trigger": ..., "label": ...}.
        if isinstance(reminder, str):
            trigger, label = reminder, summary
        else:
            trigger = reminder["trigger"]
            label = reminder.get("label") or summary
        lines += [
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{ics_escape(label)}",
            f"TRIGGER:{trigger}",
            "END:VALARM",
        ]

    lines += ["END:VEVENT", "END:VCALENDAR"]

    folded: list[str] = []
    for line in lines:
        folded.extend(fold(line))
    return "\r\n".join(folded) + "\r\n"


# --------------------------------------------------------------------------
# Landing page
# --------------------------------------------------------------------------

def image_size(path: Path) -> tuple[int, int]:
    """Read pixel dimensions from a PNG or JPEG header. Stdlib only.

    Used so the width/height attributes are read off the actual file at build
    time - swap in a different-sized logo or hero and the markup corrects
    itself instead of advertising a stale aspect ratio.
    """
    data = path.read_bytes()

    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return (
            int.from_bytes(data[16:20], "big"),
            int.from_bytes(data[20:24], "big"),
        )

    if data[:2] == b"\xff\xd8":  # JPEG
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            # SOFn frame headers carry the dimensions; C4/C8/CC are not SOF.
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                return (
                    int.from_bytes(data[i + 7:i + 9], "big"),
                    int.from_bytes(data[i + 5:i + 7], "big"),
                )
            i += 2 + int.from_bytes(data[i + 2:i + 4], "big")

    raise SystemExit(f"error: cannot read image dimensions from {path.name}")


def human_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    kb = num_bytes / 1024
    return f"{kb:.0f} KB" if kb < 1024 else f"{kb / 1024:.1f} MB"


def tel_href(phone: str) -> str:
    """Normalise an Australian number to E.164 for a tel: link."""
    digits = re.sub(r"[^\d+]", "", phone)
    if digits.startswith("+"):
        return digits
    if digits.startswith("0"):
        return "+61" + digits[1:]
    return digits


def format_date(date: dt.date) -> str:
    # %-d is unpadded on Linux/macOS; build it by hand for portability.
    return f"{date.strftime('%A')} {date.day} {date.strftime('%B %Y')}"


def download_cards(downloads: list[dict]) -> str:
    cards = []
    for item in downloads:
        path = ROOT / item["path"]
        if not path.exists():
            print(f"  ! skipping missing download: {item['path']}", file=sys.stderr)
            continue

        suffix = path.suffix.lstrip(".").upper()
        meta = f"{suffix} &middot; {human_size(path.stat().st_size)}"
        variant = "dl--primary" if item.get("primary") else "dl--secondary"

        cards.append(
            f'      <div class="dl-item">\n'
            f'        <a class="dl {variant}" href="{html.escape(item["path"])}" download>\n'
            f'          <span class="dl__label">{html.escape(item["label"])}</span>\n'
            f'          <span class="dl__meta">{meta}</span>\n'
            f"        </a>\n"
            f'        <p class="dl__desc">{html.escape(item["description"])}</p>\n'
            f"      </div>"
        )
    return "\n".join(cards)


def build_page(cfg: dict, template: str) -> str:
    ev, contact, site = cfg["event"], cfg["contact"], cfg["site"]
    date = dt.date.fromisoformat(ev["date"])

    if ev["all_day"]:
        time_text = "Reporting time to be advised"
    else:
        time_text = f"{ev['start']} &ndash; {ev['end']} AWST"

    values = {
        "EVENT_NAME": html.escape(ev["name"]),
        "TAGLINE": html.escape(site["tagline"]),
        "DATE_LONG": html.escape(format_date(date)),
        "DATE_BIG": f"{date.day} {date.strftime('%B %Y')}",
        "DATE_WEEKDAY": date.strftime("%A"),
        "DATE_ISO": date.isoformat(),
        "TIME_TEXT": time_text,
        "LOCATION": html.escape(ev["location_short"]),
        "LOCATION_FULL": html.escape(ev["location"]),
        "PARKING_NAME": html.escape(ev["parking_name"]),
        "PARKING_ADDRESS": html.escape(ev["parking_address"]),
        "PARKING_URL": html.escape(ev["parking_url"], quote=True),
        "CONTACT_TEAM": html.escape(contact["team"]),
        "CONTACT_ORG": html.escape(contact["organisation"]),
        "CONTACT_EMAIL": html.escape(contact["email"]),
        "CONTACT_PHONE": html.escape(contact["phone"]),
        "PHONE_HREF": tel_href(contact["phone"]),
        "BASE_URL": html.escape(site["base_url"].rstrip("/")),
        "DOWNLOADS": download_cards(cfg["downloads"]),
        "BUILT_ON": dt.date.today().isoformat(),
    }

    # The hero is a CSS background now, so it has no width/height attributes -
    # sizing it here anyway makes the build fail loudly if the file goes
    # missing, instead of the banner silently 404ing its background.
    for key, rel in [("LOGO", "assets/perth-airport-logo-white.png"),
                     ("HERO", "assets/hero.jpg"),
                     ("SOCIAL", "assets/social-card.jpg"),
                     ("MAP", "assets/parking-map.jpg")]:
        w, h = image_size(ROOT / rel)
        values[f"{key}_W"], values[f"{key}_H"] = str(w), str(h)

    page = re.sub(
        r"\{\{\s*(\w+)\s*\}\}",
        lambda m: values[m.group(1)] if m.group(1) in values else m.group(0),
        template,
    )

    leftover = sorted(set(re.findall(r"\{\{\s*(\w+)\s*\}\}", page)))
    if leftover:
        raise SystemExit(f"error: unknown placeholders in template: {leftover}")
    return page


# --------------------------------------------------------------------------

def write_if_changed(path: Path, content: str, *, ignore: re.Pattern | None = None) -> None:
    """Write only on a real change, so rebuilds don't churn git history.

    `ignore` masks lines that change on every build (DTSTAMP) before comparing.
    """
    new = content
    if path.exists():
        # newline="" keeps CRLF intact so the comparison sees the real bytes.
        with open(path, "r", encoding="utf-8", newline="") as fh:
            old = fh.read()
        a, b = (old, new) if ignore is None else (ignore.sub("", old), ignore.sub("", new))
        if a == b:
            print(f"  = {path.relative_to(ROOT)} (unchanged)")
            return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(new)
    print(f"  > {path.relative_to(ROOT)}")


def calendars(cfg: dict) -> list[dict]:
    """Every calendar to emit: the participant event, then any extras.

    `event` stays the participant event and is what drives the web page;
    `extra_calendars` are additional audiences (observers, staff) that share
    the same contact and site details but nothing else.
    """
    primary = dict(cfg["event"])
    primary.setdefault("output", str(ICS_OUT.relative_to(ROOT)))
    out = [primary] + [dict(e) for e in cfg.get("extra_calendars", [])]

    # A shared UID is the one mistake that would silently destroy data:
    # calendar clients key off UID, so importing the second file would
    # REPLACE the first event in the subscriber's calendar rather than add
    # to it. Same for a shared output path, which would clobber on disk.
    for field, what in [("uid", "UID"), ("output", "output path")]:
        seen: dict[str, str] = {}
        for ev in out:
            value = ev[field]
            if value in seen:
                raise SystemExit(
                    f"error: {ev['output']} and {seen[value]} share a {what} "
                    f"({value!r}). Give each calendar its own — otherwise "
                    "importing one replaces the other."
                )
            seen[value] = ev["output"]
    return out


def main() -> int:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    stamp = dt.datetime.now(dt.timezone.utc)

    print("Building Exercise Horizon 2026 site")
    for ev in calendars(cfg):
        write_if_changed(
            ROOT / ev["output"],
            build_ics(ev, cfg["contact"], cfg["site"], stamp),
            # These three carry the build clock. Masking them for the
            # comparison means they only actually change when the event
            # content does.
            ignore=re.compile(r"^(DTSTAMP|CREATED|LAST-MODIFIED):.*$\r?\n?", re.MULTILINE),
        )
    write_if_changed(PAGE_OUT, build_page(cfg, TEMPLATE.read_text(encoding="utf-8")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
