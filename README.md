# Exercise Horizon 2026

A minimal static landing page for Exercise Horizon 2026 (Perth Airport,
Emergency Operations). Its main job is **hosting relevant files** — chiefly the
calendar (`.ics`) file that the "Add to Calendar" button in the participant
emails points at.

No build tooling, no dependencies, no JavaScript on the page. One Python
script (stdlib only) generates the `.ics` and the HTML from a single config
file.

## Layout

```
event.json                     single source of truth — edit this
templates/index.html           page template ({{PLACEHOLDER}} substitution)
scripts/build.py               generates index.html + the .ics
index.html                     generated — do not edit by hand
files/
  exercise-horizon-2026.ics    generated — the calendar file
assets/
  perth-airport-logo.png       masked out of the email banner
  parking-map.jpg              walking route, Belmont S&RC -> Forster Park
  fonts/                       Lab Grotesque Light + Regular (woff2 + woff)
```

## Brand

Built to the PAPL design language taken from the Ground Transport parking
price calculator: 22px card radius, the `0 18px 50px rgba(10,73,99,.14)`
ocean shadow, clip-path shard motifs, pill actions, and the Ocean / Coast /
Hovea / Pindan palette. Teal `#19807c` — the accent from the Exercise Horizon
email — is the dominant colour, so it takes the header and primary actions
where the calculator uses Ocean; the rest of the PAPL palette is unchanged and
supports it.

**Typography is Lab Grotesque, self-hosted, with no web fallback in normal
use.** Only Light (300) and Regular (400) are licensed here, so the page builds
its hierarchy from those two weights plus size, colour and letter-spacing.
`font-synthesis: none` is set globally, which stops browsers inventing a fake
bold from Regular — that is why `<strong>` is styled with colour (and, where
the emphasis is load-bearing, an underline) rather than weight. **If you add a
Medium or Bold weight later, add the `@font-face` rule before using
`font-weight: 500`+ anywhere**, or the text will silently render at Regular.

The Perth Airport logo sits on a white bar above the teal header. The email's
copy of the logo is on a flat pale-teal field, so it was alpha-matted off that
background rather than cropped; it is 318px wide, which is sharp at the 190px
it displays at but not much beyond. If you have the official logo from the
brand library, drop it in as `assets/perth-airport-logo.png` and it will be
used as-is. A reversed (white) logo would allow dropping the white bar and
placing the logo directly on the teal.

## Making a change

Edit `event.json`, then:

```sh
python3 scripts/build.py
```

That rewrites `index.html` and `files/exercise-horizon-2026.ics`. Commit both.
The script only writes files whose content actually changed, so a no-op
rebuild leaves the working tree clean.

Prose (the "what to bring" lists, the important-information notes) lives in
`templates/index.html`. Facts that appear in more than one place (date,
location, parking, contact details, the download list) live in `event.json` so
they are stated once.

## The calendar file

Currently generated as an **all-day** event on **Thursday 17 September 2026** —
which matches the email's position that role, reporting time and location are
assigned later and sent separately. An all-day entry marks the date without
committing anyone to hours that have not been set.

To switch to a timed event once times are known, set in `event.json`:

```json
"all_day": false,
"start": "07:30",
"end": "14:00"
```

The generator then emits a timed `VEVENT` in `Australia/Perth` with a
`VTIMEZONE` block.

### Re-issuing after the date changes

Calendar clients key off `UID`. `uid` is fixed, so if you change the date and
republish, clients that already imported the event will **update** the existing
entry rather than create a second one — but only if `SEQUENCE` increases.
**Bump `sequence` in `event.json` every time you republish a changed event.**

Other fields worth knowing:

| Field | Effect |
| --- | --- |
| `busy` | `false` marks the day free (`TRANSP:TRANSPARENT`). Set `true` to block the calendar out. |
| `reminders` | RFC 5545 triggers relative to the start. Defaults fire 09:00 a week before and 09:00 the day before. |
| `status` | `CONFIRMED`, `TENTATIVE` or `CANCELLED`. Publishing with `CANCELLED` plus a bumped `sequence` withdraws the event from calendars that imported it. |

## Adding another file to host

Drop the file in `files/`, add an entry to `downloads` in `event.json`, and
rebuild:

```json
{
  "path": "files/participant-briefing.pdf",
  "label": "Participant Briefing",
  "description": "Pre-exercise briefing pack",
  "primary": false
}
```

The file type and size shown on the page are read off disk at build time, so
they stay accurate on their own. Set `"primary": true` to give an entry the
filled teal treatment — the calendar file has it now.

## Publishing

Static files, so any host works. For GitHub Pages: **Settings → Pages →
Deploy from a branch**, pick this branch and the `/` (root) folder.

The published URL must match `site.base_url` in `event.json` — it is used for
the canonical link, the social preview image and the `URL` property inside the
`.ics`. Update it if the site moves, then rebuild.

Once live, the "Add to Calendar" button in the email template replaces
`[AddToCalendarLink]` with:

```
https://<your-pages-url>/files/exercise-horizon-2026.ics
```

Linking the file directly means the button adds the date in one tap. Point it
at the site root instead if you would rather participants see the parking map
and briefing notes first.

## Contact

Exercise Planning, Emergency Operations — Emergency.Exercise@perthairport.com.au
