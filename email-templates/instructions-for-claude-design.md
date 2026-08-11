# Brief: remove embedded images from the Exercise Horizon 2026 emails

Hand this to whoever maintains the email templates. It is self-contained — no
prior context needed.

Two of the four templates are already fixed and live in this folder as worked
examples:

- `exercise-horizon-2026-attendance-confirmed.html`
- `exercise-horizon-2026-observer.html`

The **not-selected** and **reserve-list** templates still need the same
treatment.

---

## The problem

Every image was embedded in the HTML as a base64 `data:` URI. Measured on the
two originals:

| | base64 size in the HTML |
| --- | --- |
| Header | 683 KB |
| Map | 384–403 KB |
| Footer | 4 KB |
| **Total message HTML** | **~1,100 KB** |

Two independent failures result, both of which reproduce in Gmail:

1. **Gmail clips a message at roughly 102 KB** and hides the rest behind
   "View entire message". These were more than ten times that. The cut landed
   *inside* the header `<img>` tag's `src` attribute, so the tag never closed
   and everything after it rendered as raw HTML source text.
2. **Gmail does not render `data:` URI images at all.** Even an uncut message
   would have shown empty boxes.

Outlook desktop tolerates both, which is why it looked correct to the sender
and broken to the recipient. Do not judge these templates by how they look in
Outlook.

Fixing it took the two templates from ~1,100 KB to **under 30 KB** each.

---

## What to change

For every `<img>` in the template, replace the **entire** `src` attribute —
the whole `data:image/...;base64,` string, which is hundreds of thousands of
characters — with the matching hosted URL below.

```html
<!-- before -->
<img src="data:image/png;base64,iVBORw0KGgoAAAANS…(≈700,000 more chars)…" width="702">

<!-- after -->
<img src="https://nicholaspagonis.github.io/Exercise-Horizon-2026/assets/email/horizon-header.jpg"
     width="702" alt="Perth Airport - Exercise Horizon 2026">
```

Change nothing else. Leave `width`, `height`, `style`, and the surrounding
table markup exactly as they are — that markup is what makes the email render
correctly in Outlook, and it is easy to break.

## The hosted images

All four are already live. Base URL:

```
https://nicholaspagonis.github.io/Exercise-Horizon-2026/assets/email/
```

| File | What it is | Displays at | Used by |
| --- | --- | --- | --- |
| `horizon-header.jpg` | Perth Airport / Exercise Horizon 2026 banner | 702px | every template |
| `horizon-footer.png` | Teal footer band | 702px | every template |
| `horizon-map-forster-park.jpg` | Walking route, Belmont S&RC → Forster Park | 612px | participant emails |
| `horizon-map-alpha-building.jpg` | Alpha Building car park | 612px | observer email |

Each is stored at 2× its display width so it stays sharp on high-density
screens. **Match the map to the email** — the observer email uses the Alpha
Building map, not Forster Park.

The not-selected and reserve-list emails most likely use only the header and
footer. If either contains a map or any other image not listed above, do not
invent a URL: send the image to be hosted first, then reference it.

---

## Rules

1. **Never re-embed base64.** Any `data:` URI reintroduces both failures.
2. **Every `<img>` needs an `alt`.** Informative images get a real
   description; the header is `alt="Perth Airport - Exercise Horizon 2026"`.
   Decorative images get `alt=""` — the footer band is decorative, and an
   empty `alt` stops clients printing a stray placeholder label for it.
3. **Never put information only in an image.** A meaningful share of
   recipients read these with images off at least once. Dates, times,
   addresses, role details and instructions must all exist as HTML text.
   This already holds: the step tracker and the details tables are HTML, not
   pictures. Keep it that way.
4. **Do not add tracking pixels or web fonts.** They add external requests
   for no benefit here.

---

## How to verify before sending

1. **No embedded images survive.** Search the file for `data:image` — there
   must be zero matches.
2. **Size is under the clip limit.** The file must be well under 102 KB. The
   two fixed templates are 29.6 KB and 28.3 KB; anything above ~60 KB means
   something is still embedded.
3. **Every image resolves.** Open the file in a browser and confirm all
   images load from the hosted URLs.
4. **It reads with images off.** Block images in the browser and re-open. The
   email must still make sense — the reader should know what it is, when the
   exercise is, and where to go.
5. **Send a live test to one of each:** a Gmail address, an Outlook.com
   address, and an `our.ecu.edu.au` address. The recipient list is mostly
   those three. Gmail is the one that exposed this bug, so it is the one that
   matters most.

---

## Recipient mix, for context

| Client | External images | Notes |
| --- | --- | --- |
| Gmail (web and app) | Shown by default | Proxied via googleusercontent. Rejects `data:` URIs and clips at ~102 KB. |
| Outlook.com / Microsoft 365 web, including ECU | Generally shown | Can be disabled by org policy. |
| Outlook desktop (Windows) | Blocked until clicked | Applies to external senders. Internal Perth Airport recipients usually auto-download. |

Hosted images mean Outlook desktop users outside Perth Airport get a one-click
"download pictures" prompt. That is the accepted cost, and rule 3 above is
what makes it harmless.
