# Toolbar icons

Drop PNGs here and the toolbar picks them up on the next plugin restart
(toggle GS_Asset_Bridge off and on under Python > Plugins).

| File | Used for |
|---|---|
| `bridge.png` | The toolbar button that shows the panel |

A missing or unreadable icon is not an error — the button falls back to its text
label, so the toolbar always works.

**Size:** 24×24 or 32×32 PNG with transparency. Painter scales to the toolbar
height, and anything much larger just costs sharpness.

To change which filename is used, edit `TOOLBAR_ICON` at the top of
`../__init__.py`.
