# Free-Skadis

A FreeCAD Python macro that generates parametric solid storage bins for the **IKEA Skådis** pegboard system.

> Design your bin, set your dimensions, run the script — get a print-ready 3D model in seconds.

## Features

- Fully parametric — adjust width, depth, height, and wall thickness to fit any slot on your Skådis board
- Generates a solid FreeCAD Part object, ready to export as STL for 3D printing
- Correct Skådis peg geometry baked in — no measuring or guessing
- Pure Python, no external dependencies beyond FreeCAD itself

## Requirements

- [FreeCAD](https://www.freecad.org/) 0.20 or later

## Installation

1. Download `FreeSkadis.py` from this repository.
2. Open FreeCAD.
3. Go to **Macro → Macros…** and click **Create** or **Open**, then point it to the downloaded file.

Alternatively, place `FreeSkadis.py` in your FreeCAD macros folder:

| OS      | Default macros folder                              |
|---------|----------------------------------------------------|
| Linux   | `~/.FreeCAD/Macro/`                                |
| macOS   | `~/Library/Preferences/FreeCAD/Macro/`            |
| Windows | `%APPDATA%\FreeCAD\Macro\`                         |

## Usage

1. Open or create a FreeCAD document.
2. Open the macro via **Macro → Macros… → FreeSkadis → Execute**, or use the Macro editor toolbar.
3. Edit the parameters at the top of the script to match the bin size you want (see [Parameters](#parameters) below).
4. Run the macro. A solid bin body will be added to the active document.
5. Export as STL via **File → Export** and slice for printing.

## About the Skådis System

The IKEA Skådis is a pegboard with a fixed 40 mm hole-to-hole spacing. Accessories hang via a proprietary double-peg clip. This macro encodes those clip dimensions so the generated bin snaps directly onto the board without modification.

—

**Disclaimer:** This README.md was partially generated with AI assistance.
