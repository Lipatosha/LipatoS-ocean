# Ocean Third-Party Runtime Licenses

This file covers third-party runtime assets and libraries distributed with the Ocean Foundry VTT module. It intentionally lists only files included in the runtime package built into `dist/`; local planning files, tests, source asset packs, and idle assets are not part of the distribution.

## Module Code

Ocean module code and original module content are copyright Reslin unless otherwise stated.

## Boat VFX Runtime Textures

- Runtime files: `assets/boat-wake-vfx/boat-wake-foam-sheet.png`, `assets/boat-wake-vfx/boat-wake-rear-sheet.png`, `assets/boat-wake-vfx/boat-wake-side-sheet.png`
- Source: Boat VFX asset pack, Realtime VFX Store
- Creator / seller: Ben Durrant / Realtime VFX Store
- Licensed use: processed runtime textures embedded in a paid Foundry VTT module.
- Permission record: the seller confirmed by email on June 4, 2026 that the processed assets may be embedded in this module and distributed as part of it.
- Restriction: these textures may not be extracted, reused, resold, redistributed, republished, or used separately as standalone VFX assets.

## HDR Environment Map

- Runtime file: `assets/sky/citrus_orchard_road_puresky_2k.hdr`
- Title: Citrus Orchard Road Pure Sky
- Source: Poly Haven, https://polyhaven.com/a/citrus_orchard_road_puresky
- License: CC0.

## 3D Ship Models

Runtime files under `assets/model/` are CC BY 4.0 ship models used by Ocean and Scenic 3D. The original attribution text is preserved in each model folder's `license.txt` file and must remain with the distributed package.

- `assets/model/viking_ship/` — emelyarules
- `assets/model/caravel_ship/` — Ginny Sutton
- `assets/model/dutch_ship/` — m23ldx0191
- `assets/model/empty_ship/` — Liaval
- `assets/model/pirate_ship/` — Kimagure_Cookie
- `assets/model/ship_aa/` — gogiart
- `assets/model/ship_b/` — gogiart
- `assets/model/ship_y/` — gogiart

## Runtime JavaScript Libraries

- `lib/EXRLoader.js` and `lib/RGBELoader.js` are Three.js loader modules. Their source files retain upstream copyright and license notices.
- `lib/fflate.module.js` is fflate 0.6.9, licensed under MIT. The source file retains its upstream license header.

## Not Distributed

The `dist/` package does not include idle assets, source asset packs, local planning notes, tests, development scratch folders, or any files under the module's local idle folder.