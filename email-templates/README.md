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

## One trade-off

Hosted images are external references, so some clients (Outlook desktop
especially) hide them behind a "Click here to download pictures" prompt until
the recipient allows them. That is the normal cost of hosting, and the emails
are written to read correctly with images off — every image carries `alt`
text and no image contains information that only exists in the picture.
