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
  hero.jpg                     header photograph
  social-card.jpg              1200x630 link-preview card (og:image)
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

### Graphic thread

The header carries the page's **one** graphic-thread composition, built to the
layering approach in the 2025 brand guidelines and matching the reference
composition supplied by the brand team:

- The image is cropped to a **quadrilateral** with a steep left edge — two
  triangles forming a "point", one of the shapes deconstructed from the
  facets — bleeding off the right.
- A **single-colour Coast quadrilateral sits behind** it on a deliberately
  opposed angle, so it shows only at two opposite ends: a wedge above the
  frame's top edge and a band below its lower-left corner.
- The left of the header stays a **large unobstructed content area**.

Both shapes use percentage `clip-path` and the composition is anchored to all
four edges of the teal banner, so it spans the banner's **full height** at
every width — the frame meets the banner's top-right and bottom-right corners,
and the Coast band runs to the bottom edge.

**Below 900px the composition is dropped entirely.** On a phone it pushed the
downloads — the reason people open this page — well below the fold. The frame
is a CSS `background-image` rather than an `<img>` specifically so that
`display: none` also skips the request; a hidden `<img>` is still downloaded.
Phones therefore never fetch the 198 KB hero at all.

Deliberately **not** done, per the guidelines: the facets are never recreated,
modified, tiled, overlapped or given effects, and the shapes are not repeated
elsewhere on the page — which is why the footer is a plain rule and the old
floating background shard is gone. If you need a variation, the guidelines
direct advanced compositions through the Brand & Marketing team.

`assets/hero.jpg` is the supplied photograph, cropped to 3000×2000 from the
left edge of the 3607×2405 original and resized to 1600×1067 at quality 82 —
193 KB. The crop is what positions the firefighter inside the frame: the image
and the art box are near enough the same aspect that `object-fit` has only
about 40px of horizontal play, so `object-position` alone cannot move the
subject meaningfully. To shift him further right, widen the crop's right
margin; to shift him left, start the crop further right. The full-resolution
original is in git history at commit 36557fb.

**Typography is Lab Grotesque, self-hosted, with no web fallback in normal
use.** Only Light (300) and Regular (400) are licensed here, so the page builds
its hierarchy from those two weights plus size, colour and letter-spacing.
`font-synthesis: none` is set globally, which stops browsers inventing a fake
bold from Regular — that is why `<strong>` is styled with colour (and, where
the emphasis is load-bearing, an underline) rather than weight. **If you add a
Medium or Bold weight later, add the `@font-face` rule before using
`font-weight: 500`+ anywhere**, or the text will silently render at Regular.

The banner runs from the top of the page — there is no white logo bar, and no
brandline above the title, since the reversed logo already says Perth Airport.
`assets/perth-airport-logo-white.png` is the official reversed mark, resized to
640px wide: it displays at 190px, so 640 covers a 3x screen while the 2194px
original was 11.5x oversampled. `perth-airport-logo.png` (full colour) is no
longer used by the page but is kept for light backgrounds. `build.py` reads
both files' dimensions off disk, so replacing either needs no other change.

### Link previews

`og:image` points at `assets/social-card.jpg`, a dedicated 1200×630 crop of the
hero photograph. **Do not point it at the parking map.** The map is participant
wayfinding — it names the venue and the parking area — and as the `og:image` it
was being rendered into every iMessage, Slack and Teams preview of the link.
1200×630 is also the aspect previewers expect, so nothing gets cropped
arbitrarily. Regenerate the card from `hero.jpg` if the photograph changes.

### Selection Process diagram

The branching flow in the Selection Process card is plain HTML and CSS — no
SVG diagram, no JavaScript. Node centres sit at 1/6, 3/6 and 5/6 of the width,
so the fork lands at 33.3% (between the first two nodes) and the elbow ends at
50% (the reserve node's centre). All geometry derives from `--dot`, `--lh` and
`--row` on `.flow`, which is why the same two connector elements stay aligned
from 320px to 1920px without a second layout. If you add or remove a node,
update the three percentages in `.flow__spine` and `.flow__elbow` to match the
new column count.

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

A timed `VEVENT` on **Thursday 17 September 2026, 07:00–14:00 AWST**, in
`Australia/Perth` with a `VTIMEZONE` block. Set `"all_day": true` to fall back
to a date-only entry that marks the day without committing to hours.

The summary is deliberately **not** the same string as the page title:

```json
"name":        "Exercise Horizon 2026",
"ics_summary": "[AWAITING EXTRA INFO] Exercise Horizon 2026"
```

`name` drives the page and `X-WR-CALNAME`; `ics_summary` drives the event's
`SUMMARY`, so the prefix appears in people's calendars without appearing as
the page heading. **Drop the prefix from `ics_summary` once roles and reporting
times go out**, bump `sequence`, and republish — imported entries will rename
themselves.

### More than one calendar

`event` is the participant event and also drives the web page. Additional
audiences go in `extra_calendars`, each a full event definition plus an
`output` path; they inherit only `contact` and `site`. There is currently one:
`files/exercise-horizon-2026-observer.ics`, the observer day — different venue
(Airport Experience Centre), different hours (08:00–13:15) and a bus circuit
rather than a single location.

**Every calendar needs its own `uid`.** Clients key off `UID`, so two files
sharing one means importing the second *replaces* the first in the
subscriber's calendar instead of adding to it. The build refuses to run if two
calendars share a `uid` or an `output` path, so that mistake cannot ship
quietly.

The observer file is hosted but deliberately **not** listed in `downloads` —
that list renders on the participant page, and an observer entry there invites
participants to add the wrong event. The observer email links the file
directly:

```
https://<pages-url>/files/exercise-horizon-2026-observer.ics
```

### Re-issuing after the date changes

Calendar clients key off `UID`. `uid` is fixed, so if you change the date and
republish, clients that already imported the event will **update** the existing
entry rather than create a second one — but only if `SEQUENCE` increases.
**Bump `sequence` in `event.json` every time you republish a changed event.**

Other fields worth knowing:

| Field | Effect |
| --- | --- |
| `busy` | `true` blocks the calendar out (`TRANSP:OPAQUE`, Outlook busy). `false` marks it free — useful for a date-marker entry. |
| `reminders` | A list of `{"trigger", "label"}` objects, or bare RFC 5545 trigger strings. Triggers are relative to the start, so `-P7D` on an 07:00 event fires 07:00 seven days earlier. Currently two weeks, one week and one day out. |
| `status` | `CONFIRMED`, `TENTATIVE` or `CANCELLED`. Publishing with `CANCELLED` plus a bumped `sequence` withdraws the event from calendars that imported it. |
| `categories` | `CATEGORIES`, for people who filter or colour-code their calendar. |
| `contact.organizer_cn` | The `ORGANIZER` display name, kept separate from `contact.team` so the calendar and the page can name different groups. **Avoid commas.** They are quoted correctly (`CN="A, B"`, since parameter values quote rather than backslash-escape), but Apple Calendar reads a comma in a `CN` as `Last, First` and reorders the name — `Exercise Planning, Perth Airport` displayed as *Perth Exercise Planning* on iOS. |

`CREATED` and `LAST-MODIFIED` are emitted alongside `DTSTAMP`. All three carry
the build clock, so the build masks them when deciding whether to rewrite the
file — meaning they change only when the event content actually changes, and a
no-op rebuild still leaves the tree clean.

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

Emergency Operations, Perth Airport — Emergency.Exercise@perthairport.com.au
