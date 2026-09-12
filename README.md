# Totem Compass firmware — reverse engineering

Independent, unofficial reverse-engineering notes for the **Totem Compass** ESP32
firmware (**v5.0.2**), produced entirely by static analysis of a publicly downloadable
firmware image and the companion mobile app. Not affiliated with or endorsed by Totem Labs.

## Key findings

- The device is an **ESP32** (Xtensa LX6) running **MicroPython v1.25.0** on **ESP-IDF v5.4**.
- Totem's application is **Python**, frozen into the image as bytecode across **98 modules**.
- Three radios share the 2.4 GHz band: **BLE** (phone app), **ESP-NOW** ("Unity Mesh",
  Totem-to-Totem), and **WiFi** (hotspot OTA).
- Application messages use a shared `(cat_id, cmd_id)` model with a common chunking layer.

## Documentation

Full docs live in [`docs/`](docs/) as a [Mintlify](https://mintlify.com) site.

```bash
cd docs
npm i -g mint    # or: npx mint@latest
mint dev         # preview at http://localhost:3000
```

Start at [`docs/index.mdx`](docs/index.mdx). The 2.4 GHz protocol capture — with a
completeness matrix — is under [`docs/protocols/`](docs/protocols/).

## Scope & ethics

All analysis is static: no code was executed on a device and no service was attacked.
The releases API and firmware objects are served publicly. See
[`docs/reference/methodology.mdx`](docs/reference/methodology.mdx).
