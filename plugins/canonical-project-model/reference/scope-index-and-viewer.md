# Scope Index, Index Legend and the Live Viewer

**Purpose:** index the drawing set once, deterministically, so every later step
reads the same structured facts, and show them in one viewer and one linked PDF.

```
 drawing PDFs
      |
      v
 build_atlas_data.py   sheets, callouts, words          sections/plans_atlas.json
      |
      v
 scope_index.py        project index, notes,            sections/scope_index.json
      |                clarifications, schedules,       atlas/crops/*.jpg
      |                scope index per trade
      v
 build_atlas_html.py   viewer (Document Engine shell)   Plans Atlas/plans-atlas.html
 build_atlas_pdf.py    Index Legend in front + links    Plans Atlas/<set> - Plans Atlas.pdf
      |                                                 Plans Atlas/Index Legend.pdf, INDEX-LEGEND.md
      v
 interlink.py          knowledge-base records           <kb>/atlas/atlas-chunks.json
 phase1_receiver.py    legend + scope index copies      <kb>/atlas/Index Legend.pdf, scope_index.json
```

`deploy_atlas.py` runs all of it. Nothing here calls a model or the network.

## What the scope index holds

- **Project Index:** project title, address, owner, architect, MEP engineer, other
  engineers; the page index (page, sheet, title, detail labels and titles); general
  and sheet notes per page; rooms (number, name, SF where printed, perimeter);
  millwork elevations; subcontractor trades.
- **Clarifications and Exclusions:** every note sorted under **scheduling**,
  **exclusions**, **owner-required vendors**, **owner allowances**, **pricing and
  alternates**, **phasing**, with its page and related trades. Sorted by keyword;
  a note can sit under more than one header.
- **Schedules:** each schedule on the sheets as a cropped image **and** a recreated
  table: door, door hardware, window, finish, lighting, electrical equipment,
  plumbing fixture, HVAC equipment, fire alarm, millwork, equipment, room.
- **Scope index per CSI division:** its schedules, notes, sheets, size tags and
  takeoff quantities. Extra detail for **doors** (door marks located on the plans,
  door elevations, finish schedule rows linked to their spec chapter) and
  **millwork** (each elevation with its cabinet codes, finish codes and printed
  dimensions).

## Rules it keeps

- **Never invent.** A value that is not printed is `null`, with the reason beside
  it. Room SF appears only where the plan prints it; room perimeter is never
  printed, so it is `null`.
- **Size tags are counted, not measured.** Duct, pipe, conduit and wire sizes are
  listed with how many times each tag is printed. A measured length comes only
  from the quantity takeoff (`sections/quantity_takeoff.json`).
- **Millwork counts and lengths are not measured.** The index lists what is printed
  as text on each elevation; cabinet counts, linear feet and depths stay `null`.
- **Everything is traceable.** Each record carries sheet, page and box, so it
  opens on the drawing: viewer `#sheet=<id>&box=x0,y0,x1,y1`, PDF named destination.
- **Heuristics are labelled.** A schedule rebuilt from text columns (no ruling
  lines) has confidence 0.5 and is listed in `needs_review`.

## Intra-document links: named destinations

Research summary and the method used:

- **Page-number links are the weak option.** They break when pages are inserted,
  reordered or re-issued, and cannot be addressed from outside the file.
- **Named destinations are the reliable option** (Adobe's own guidance): a link
  points at a name, the name points at a page and position. Re-issue a sheet and
  only the name's target moves. They are also addressable from outside:
  `set.pdf#nameddest=sheet:A-101`.
- **Write explicit numbers.** A `null` in the `/XYZ` view breaks pdf.js and older
  outline parsers, so every destination is written as `[page /XYZ x y 0]`.

So `build_atlas_pdf.py` writes one name tree (`/Names /Dests`) and every link is
`GoTo <name>`:

| Name | Target |
| --- | --- |
| `sheet:<sheet number>` | top of that sheet |
| `schedule:<schedule id>` | the schedule's corner on its sheet |
| `index:<section>` | that section of the Index Legend |

It also writes an **outline** (legend sections, then every sheet) and **page
labels**, so the viewer's page box shows `A-101`, not `47`. The Index Legend goes
**in front of the first drawing**; named links are unaffected by the insertion.
`compress_pdf.py` keeps all of it and refuses to write a file that lost a link.

## The viewer: NTXP Document Engine shell

Drawings and pop-up cards (search results, toast, tooltip) keep their original
look. Everything around them follows the Document Engine standard:

- **Header (persistent):** navy band, NTXP logo, title lockup, Accent Red band.
- **Second line:** every page number and title in a swipeable strip; the open
  page is highlighted and scrolled into view; arrow keys step through pages.
- **Left drawer** (hamburger, header left): Trades, Spec #, Areas, Phases.
- **Right drawer** (hamburger, header right): the bottom level of the left
  selection. A trade shows its scope summary, takeoffs, schedules (image and
  table), size tags, door marks, millwork elevations, notes and clarifications.
  A spec number shows its chapter, sheets and the finishes that cite it.
- **Mobile:** both drawers slide over the page with a scrim; the strip swipes.

## Live overlays, export and print

Overlays follow the **NTXP PDF markup standard** (`ntxp-pdf-markups-and-redlines`):
hue carries the trade; demolition is dotted with a 25% fill; new work is solid
with a 40% fill; measurements are red; line markups get a focus halo.

- **Layers:** Markups (on by default), Schedules, Notes, Rooms, Door Marks (off
  by default, so a sheet opens exactly as drawn).
- **Markups** are read from `model/atlas/markups/*.json`, markup manifest schema
  3.0 (or the 1.0 geometry body). Kinds the viewer cannot draw (signature, stamp,
  screenshot) are reported, never dropped silently.
- **Animated:** outlines draw in, fills fade in; reduced-motion is respected.
- **Export:** sheet image with overlays (PNG), the visible markups as a schema
  3.0 manifest (JSON), or the sheet with markups as a vector PDF.
- **Print:** the open sheet with its overlays, or the sheet index.
- **PDF export needs the live server:** `python scripts/atlas_live.py serve
  --project <dir>` (local only), or `atlas_live.py export --sheet A-101`.

A viewer export is a working copy. A markup that leaves the building is still
published by `ntxp-pdf-markups-and-redlines`, which owns the audited output.

## Limits to know

- Schedules, notes, rooms and details are found by layout rules. Unusual title
  blocks or schedules drawn as images will be missed; `needs_review` says what
  was low-confidence, not what was missed.
- Scanned sheets with no text layer are indexed only as far as OCR reads them.
- Measured quantities (duct, pipe, conduit, wire, flooring, cabinet counts) are
  out of scope here by design; they come from the takeoff.
