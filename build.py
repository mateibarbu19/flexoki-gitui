#!/usr/bin/env python3
"""Build the GitUI themes: theme.ron variants, and matching .tmTheme syntax themes.

The .ron palette lives here, transcribed from kepano/flexoki's
_generators/src/palette.ts. The syntax themes are converted from
kepano/flexoki-sublime, whose .sublime-color-scheme files already carry ~115
TextMate scope rules; pass --sublime to point at a checkout of that repo.

Standard library only.

  ./build.py                            # theme.ron variants only
  ./build.py --sublime ../flexoki-sublime   # ... plus .tmTheme variants
"""

import argparse
import json
import plistlib
import re
import sys
import uuid
from pathlib import Path

# token -> (light, dark), in Flexoki's semantic UI naming. The accent -2 tokens
# are the opposite-tone accents, used when a color needs to sit back a step.
# $syntax is the .tmTheme basename GitUI looks up, not a color.
PALETTE = {
    "bg": ("#fffcf0", "#100f0f"),
    "bg-2": ("#f2f0e5", "#1c1b1a"),
    "ui": ("#e6e4d9", "#282726"),
    "ui-2": ("#dad8ce", "#343331"),
    "ui-3": ("#cecdc3", "#403e3c"),
    "tx-3": ("#b7b5ac", "#575653"),
    "tx-2": ("#6f6e69", "#878580"),
    "tx": ("#100f0f", "#cecdc3"),
    "re": ("#af3029", "#d14d41"),
    "or": ("#bc5215", "#da702c"),
    "ye": ("#ad8301", "#d0a215"),
    "gr": ("#66800b", "#879a39"),
    "cy": ("#24837b", "#3aa99f"),
    "bl": ("#205ea6", "#4385be"),
    "pu": ("#5e409d", "#8b7ec8"),
    "ma": ("#a02f6f", "#ce5d97"),
    "re-2": ("#d14d41", "#af3029"),
    "or-2": ("#da702c", "#bc5215"),
    "ye-2": ("#d0a215", "#ad8301"),
    "gr-2": ("#879a39", "#66800b"),
    "cy-2": ("#3aa99f", "#24837b"),
    "bl-2": ("#4385be", "#205ea6"),
    "pu-2": ("#8b7ec8", "#5e409d"),
    "ma-2": ("#ce5d97", "#a02f6f"),
    "syntax": ("flexoki-light", "flexoki-dark"),
}

VARIANTS = ("light", "dark")

# Matches a whole token, so $tx-2 can never be clipped to $tx by an earlier rule.
TOKEN = re.compile(r"\$[a-z]+(?:-\w+)?")

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "dist"


# --------------------------------------------------------------------------- ron


def resolve(template: str, variant: str) -> str:
    """Substitute every $token for its value in the given variant."""
    index = VARIANTS.index(variant)
    unknown = set()

    def replace(match: re.Match) -> str:
        token = match.group()[1:]
        if token not in PALETTE:
            unknown.add(token)
            return match.group()
        return PALETTE[token][index]

    resolved = TOKEN.sub(replace, template)
    if unknown:
        sys.exit(f"error: unknown token(s) in template.ron: {sorted(unknown)}")
    return resolved


def build_ron() -> None:
    template = (ROOT / "template.ron").read_text(encoding="utf-8")

    # Drop the template's own header comment; each variant gets its own below.
    if "(\n" not in template:
        sys.exit("error: template.ron has no opening '('")
    rest = "(\n" + template.split("(\n", 1)[1]

    for variant in VARIANTS:
        content = (
            f"// Generated from template.ron by build.py — do not edit.\n"
            f"// Flexoki {variant}. Regenerate instead: ./build.py\n"
            f"{resolve(rest, variant)}"
        )
        path = OUT_DIR / f"flexoki-{variant}.ron"
        path.write_text(content, encoding="utf-8")
        print(f"built {path.relative_to(ROOT)}")


# ----------------------------------------------------------------------- tmTheme

SUBLIME_FILES = {
    "light": "Flexoki Light.sublime-color-scheme",
    "dark": "Flexoki Dark.sublime-color-scheme",
}

# Sublime's globals are snake_case; TextMate's are camelCase. Keys absent here
# have no TextMate equivalent (accent, fold_marker, block_caret, ...) and are
# dropped rather than guessed at.
GLOBALS = {
    "background": "background",
    "foreground": "foreground",
    "caret": "caret",
    "invisibles": "invisibles",
    "line_highlight": "lineHighlight",
    "selection": "selection",
    "selection_border": "selectionBorder",
    "inactive_selection": "inactiveSelection",
    "inactive_selection_foreground": "inactiveSelectionForeground",
    "misspelling": "misspelling",
    "gutter": "gutter",
    "gutter_foreground": "gutterForeground",
    "highlight": "highlight",
    "find_highlight": "findHighlight",
    "find_highlight_foreground": "findHighlightForeground",
    "guide": "guide",
    "active_guide": "activeGuide",
    "stack_guide": "stackGuide",
    "brackets_foreground": "bracketsForeground",
    "brackets_options": "bracketsOptions",
    "bracket_contents_foreground": "bracketContentsForeground",
    "bracket_contents_options": "bracketContentsOptions",
    "tags_foreground": "tagsForeground",
    "tags_options": "tagsOptions",
    "shadow": "shadow",
    "minimap_border": "minimapBorder",
}

VAR = re.compile(r"var\(([^()]+)\)")
ALPHA = re.compile(r"^color\(\s*(#[0-9A-Fa-f]{6})\s+alpha\(\s*([0-9.]+)\s*\)\s*\)$")
BLEND = re.compile(
    r"^color\(\s*(#[0-9A-Fa-f]{6})\s+blend\(\s*(#[0-9A-Fa-f]{6})\s+([0-9.]+)%\s*\)\s*\)$"
)
HEX = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")


def strip_jsonc(text: str) -> str:
    """Drop // and /* */ comments and trailing commas, respecting string literals."""
    out = []
    i, n = 0, len(text)
    in_string = False
    while i < n:
        c = text[i]
        if in_string:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_string = False
            i += 1
            continue
        if c == '"':
            in_string = True
            out.append(c)
            i += 1
            continue
        if text.startswith("//", i):
            i = text.find("\n", i)
            if i == -1:
                break
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        out.append(c)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def expand_hex(value: str) -> str:
    if len(value) == 4:  # #RGB
        return "#" + "".join(c * 2 for c in value[1:]).upper()
    return "#" + value[1:].upper()


def resolve_color(value: str, variables: dict[str, str]) -> str:
    """Resolve Sublime var() indirection and color() functions to a hex string."""
    seen = 0
    while VAR.search(value):
        seen += 1
        if seen > 16:
            sys.exit(f"error: cyclic variable reference in {value!r}")
        value = VAR.sub(lambda m: variables.get(m.group(1), m.group(0)), value)
        if VAR.search(value) and all(
            m.group(1) not in variables for m in VAR.finditer(value)
        ):
            sys.exit(f"error: undefined Sublime variable in {value!r}")

    value = value.strip()

    if m := HEX.match(value):
        return expand_hex(value)

    # color(<c> alpha(<a>)) -> #RRGGBBAA
    if m := ALPHA.match(value):
        base, alpha = expand_hex(m.group(1)), float(m.group(2))
        return f"{base}{round(alpha * 255):02X}"

    # color(<c1> blend(<c2> P%)) -> P% of c1 over c2, flattened to a solid color
    if m := BLEND.match(value):
        c1, c2, pct = expand_hex(m.group(1)), expand_hex(m.group(2)), float(m.group(3))
        p = pct / 100
        mixed = (
            round(p * int(c1[k : k + 2], 16) + (1 - p) * int(c2[k : k + 2], 16))
            for k in (1, 3, 5)
        )
        return "#" + "".join(f"{v:02X}" for v in mixed)

    sys.exit(f"error: unsupported color expression {value!r}")


def build_tmtheme(sublime_dir: Path) -> None:
    for variant in VARIANTS:
        src = sublime_dir / SUBLIME_FILES[variant]
        if not src.is_file():
            sys.exit(f"error: {src} not found — is --sublime pointing at flexoki-sublime?")

        scheme = json.loads(strip_jsonc(src.read_text(encoding="utf-8")))
        variables = scheme.get("variables", {})

        def color(value: str, key: str = "") -> str:
            # *_options hold style keywords ("underline"), not colors.
            return value if key.endswith("_options") else resolve_color(value, variables)

        settings: list[dict] = [
            {
                "settings": {
                    GLOBALS[k]: color(v, k)
                    for k, v in scheme.get("globals", {}).items()
                    if k in GLOBALS
                }
            }
        ]

        for rule in scheme.get("rules", []):
            entry: dict[str, object] = {}
            if "name" in rule:
                entry["name"] = rule["name"]
            entry["scope"] = rule["scope"]

            body = {}
            if "foreground" in rule:
                body["foreground"] = color(rule["foreground"])
            if "background" in rule:
                body["background"] = color(rule["background"])
            if "font_style" in rule:
                body["fontStyle"] = rule["font_style"]
            entry["settings"] = body
            settings.append(entry)

        name = scheme.get("name", f"Flexoki {variant.title()}")
        plist = {
            "name": name,
            "author": scheme.get("author", "kepano"),
            "colorSpaceName": "sRGB",
            "semanticClass": f"theme.{variant}.flexoki",
            # Derived from the name so rebuilds stay byte-identical.
            "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, f"flexoki-gitui/{name}")),
            "settings": settings,
        }

        path = OUT_DIR / f"flexoki-{variant}.tmTheme"
        with path.open("wb") as fh:
            plistlib.dump(plist, fh, sort_keys=False)
        print(f"built {path.relative_to(ROOT)} ({len(settings) - 1} scope rules)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--sublime",
        type=Path,
        metavar="DIR",
        help="checkout of kepano/flexoki-sublime; enables .tmTheme output",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    build_ron()

    if args.sublime:
        build_tmtheme(args.sublime)
    else:
        print("note: --sublime not given, leaving dist/*.tmTheme untouched")


if __name__ == "__main__":
    main()
