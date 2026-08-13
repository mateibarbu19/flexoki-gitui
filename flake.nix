{
  description = "Flexoki for GitUI — light and dark themes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    # Source for the .tmTheme syntax themes: kepano's own Sublime port, whose
    # .sublime-color-scheme files already carry the TextMate scope rules.
    flexoki-sublime = {
      url = "github:kepano/flexoki-sublime";
      flake = false;
    };
  };

  outputs =
    { self, nixpkgs, flexoki-sublime }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];

      forAllSystems =
        f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      packages = forAllSystems (
        pkgs:
        let
          inherit (pkgs) lib;

          # Only the two files the build actually reads, so editing the readme
          # doesn't invalidate the derivation.
          src = lib.fileset.toSource {
            root = ./.;
            fileset = lib.fileset.unions [
              ./build.py
              ./template.ron
            ];
          };

          themes = pkgs.stdenvNoCC.mkDerivation {
            pname = "flexoki-gitui";
            version = "0.1.0";
            inherit src;

            nativeBuildInputs = [ pkgs.python3 ];

            buildPhase = ''
              runHook preBuild
              python3 build.py --sublime ${flexoki-sublime}
              runHook postBuild
            '';

            installPhase = ''
              runHook preInstall
              install -Dm644 -t $out/share/flexoki-gitui \
                dist/flexoki-light.ron dist/flexoki-dark.ron \
                dist/flexoki-light.tmTheme dist/flexoki-dark.tmTheme
              runHook postInstall
            '';

            meta = {
              description = "Flexoki theme for GitUI, light and dark variants";
              homepage = "https://github.com/mateibarbu19/flexoki-gitui";
              license = lib.licenses.mit;
              platforms = lib.platforms.all;
            };
          };

          # Laid out exactly as GitUI's config folder expects: theme.ron plus the
          # tmTheme whose basename theme.ron's `syntax` key points at. Copy the
          # whole thing into ~/.config/gitui and both take effect.
          variant =
            name:
            pkgs.runCommand "flexoki-${name}-gitui" { inherit (themes) meta; } ''
              install -Dm644 ${themes}/share/flexoki-gitui/flexoki-${name}.ron $out/theme.ron
              install -Dm644 -t $out ${themes}/share/flexoki-gitui/flexoki-${name}.tmTheme
            '';
        in
        {
          default = themes;
          flexoki-gitui = themes;
          light = variant "light";
          dark = variant "dark";
        }
      );

      # Nothing generated is committed, so there is no drift to guard against —
      # this just makes `nix flake check` actually build both variants.
      checks = forAllSystems (pkgs: {
        build = self.packages.${pkgs.system}.default;
      });

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShellNoCC {
          packages = [
            pkgs.python3
            pkgs.gitui
          ];
        };
      });
    };
}
