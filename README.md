# Flexoki for GitUI

An inky color scheme for prose and code — light and dark variants for
[GitUI](https://github.com/gitui-org/gitui).

*Disclaimer*: I have made this repo with Claude Opus 5. The end result looks
good to me.

## Install

The themes are generated rather than committed, so build them first. With Nix:

```sh
nix build github:mateibarbu19/flexoki-gitui#dark
install -Dm644 result/* -t ~/.config/gitui/
```

Or with Python, which needs a checkout of [flexoki-sublime][sublime] for the
syntax colors:

```sh
git clone https://github.com/mateibarbu19/flexoki-gitui.git
git clone https://github.com/kepano/flexoki-sublime.git
cd flexoki-gitui && ./build.py --sublime ../flexoki-sublime
cp dist/flexoki-dark.ron     ~/.config/gitui/theme.ron
cp dist/flexoki-dark.tmTheme ~/.config/gitui/
```

Swap `dark` for `light` on a light terminal. Files role:

- `theme.ron`: colors the UI
- `.tmTheme`: colors source in the file and blame views

Without the second, GitUI silently falls back to a built-in theme.

GitUI reads `~/.config/gitui/`, or `%APPDATA%/gitui/` on Windows. The terminal's
own background shows through wherever the theme doesn't paint, so pair this with
a Flexoki terminal theme from
[kepano/flexoki](https://github.com/kepano/flexoki).

### home-manager

```nix
{
  inputs.flexoki-gitui.url = "github:mateibarbu19/flexoki-gitui";

  xdg.configFile."gitui".source =
    inputs.flexoki-gitui.packages.${pkgs.system}.dark;
}
```

`#light` and `#dark` are laid out exactly like GitUI's config folder. `#default`
ships both variants under `share/flexoki-gitui/` instead.

## Color mapping

Added lines are cyan rather than the conventional green, which keeps the
add/delete pair legible under red-green color blindness.

Two deliberate choices: `use_selection_fg` is `false`, so a selected diff line
keeps its add/delete color instead of being flattened to `selection_fg`; and
`disabled_fg` is faint on purpose (2.0:1 in light), because GitUI uses it for
unfocused borders. Raise it to `$tx-2` if you want diff hunk headers louder.

## Development

Edit `template.ron` — never `dist/`, which is generated and git-ignored.

The `.tmTheme` files are converted from [flexoki-sublime][sublime], pinned as a
flake input, so the syntax colors come from the palette's author rather than
being invented here. The files should also work in `bat`, `delta` or Sublime.

## Credits

- [Flexoki](https://stephango.com/flexoki) by
  [Steph Ango](https://stephango.com)
- Syntax scopes from [flexoki-sublime][sublime], also by Steph Ango (MIT)
- Repo structure inspired by
  [rose-pine-gitui](https://github.com/charliettaylor/rose-pine-gitui)

[sublime]: https://github.com/kepano/flexoki-sublime
