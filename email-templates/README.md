# Email templates

Outlook-ready HTML for the Exercise Horizon 2026 participant emails, with the
images **hosted** rather than embedded as `data:` URIs.

## Why

The originals carried every image as base64 inside the HTML:

| | base64 size |
| --- | --- |
| Header | 683 KB |
| Map | 384–403 KB |
| Footer | 4 KB |
| **Message HTML** | **~1,100 KB** |

Gmail clips a message at roughly **102 KB** and fetches the rest behind a
"View entire message" link — so these were over ten times the limit, and the
clip landed *mid-attribute* inside the header `<img>`. A broken tag meant
everything after it rendered as raw text. Gmail also does not render `data:`
URI images, so even an uncut message would have shown gaps. Outlook desktop
tolerates both, which is why it looked fine when sent.

Hosting the images fixes both causes at once:

| Template | Before | After |
| --- | --- | --- |
| Attendance confirmed | 1,100 KB | **29.6 KB** |
| Observer | 1,118 KB | **28.2 KB** |

## Hosted image URLs

```
https://nicholaspagonis.github.io/Exercise-Horizon-2026/assets/email/horizon-header.jpg
https://nicholaspagonis.github.io/Exercise-Horizon-2026/assets/email/horizon-footer.png
https://nicholaspagonis.github.io/Exercise-Horizon-2026/assets/email/horizon-map-forster-park.jpg
https://nicholaspagonis.github.io/Exercise-Horizon-2026/assets/email/horizon-map-alpha-building.jpg
```

Each is sized at 2x its display width, so it stays sharp on high-density
screens: the header renders at 702px and is 1404px, the maps render at 612px
and are ~1224px.

## Applying this to the other templates

For the not-selected and reserve-list emails, replace the whole
`src="data:image/...;base64,..."` attribute — the entire string, which is
hundreds of thousands of characters — with the matching URL above. Change
nothing else. Then confirm the file is under 102 KB.

## Recipient mix

The list is mostly Gmail, Outlook and `our.ecu.edu.au` (ECU, on Microsoft
365). Behaviour across those three:

| Client | External images | Notes |
| --- | --- | --- |
| Gmail (web and app) | Shown by default | Proxied via googleusercontent since 2013. Will **not** render `data:` URIs, and clips at ~102 KB — hosting is the only option that works here at all. |
| Outlook.com / M365 web (incl. ECU) | Generally shown | Can be turned off by org policy. |
| Outlook desktop (Windows) | Blocked until clicked | Applies to senders outside the organisation. Internal Perth Airport recipients usually auto-download. |

Because a share of recipients will read these with images off at least once,
the emails are built to survive it. Everything load-bearing is HTML text, not
pixels: the step tracker, the details table (role, arrival time, location,
parking address) and the important-information list all render with images
blocked. The only thing lost is the map, and its street address sits in the
table directly above it.

## One trade-off

Hosted images are external references, so some clients (Outlook desktop
especially) hide them behind a "Click here to download pictures" prompt until
the recipient allows them. That is the normal cost of hosting, and the emails
are written to read correctly with images off — every image carries `alt`
text and no image contains information that only exists in the picture.
