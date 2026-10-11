"""Export standalone, themed SVGs through Archify's own viewer export action."""
from __future__ import annotations

import sys
from pathlib import Path
import xml.etree.ElementTree as ET

from playwright.sync_api import sync_playwright


def export(html_path: Path, svg_path: Path) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(accept_downloads=True)
        page.goto(html_path.resolve().as_uri(), wait_until="load")
        page.locator('button[aria-controls="export-menu"]').click()
        with page.expect_download() as pending:
            page.locator('#export-menu button[data-format="svg"]').click()
        pending.value.save_as(svg_path)
        browser.close()

    xml_root = ET.parse(svg_path).getroot()
    svg_ns = "http://www.w3.org/2000/svg"
    if xml_root.tag != f"{{{svg_ns}}}svg":
        raise RuntimeError(f"Archify SVG export has no SVG root namespace: {svg_path}")
    styles = [element.text or "" for element in xml_root.findall(f"{{{svg_ns}}}style")]
    style_text = "\n".join(styles)
    if "@font-face" not in style_text or "prefers-color-scheme" not in style_text:
        raise RuntimeError(f"Archify standalone export is missing font/theme styles: {svg_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python tools/export_svgs.py <diagram.html> <diagram.svg>")
    export(Path(sys.argv[1]), Path(sys.argv[2]))
