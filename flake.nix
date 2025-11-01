# flake.nix (Corrected Structure)
{
  description = "A Nix and Python development environment with uv";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "aarch64-darwin" "x86_64-darwin" "x86_64-linux" ];
      forAllSystems = function: nixpkgs.lib.genAttrs supportedSystems (system: function nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAllSystems (pkgs:
        let
          python = pkgs.python3;
        in
        {
          default = pkgs.mkShell {
            buildInputs = [
              python
              pkgs.uv
              pkgs.ruff
            ];

            shellHook = ''
              export EDITOR="vim";
              # Set the PYTHONPLATFORM to work correctly on macOS
              export PYTHONPLATFORM="darwin"
              if [ ! -d ".venv" ]; then
                echo "Creating new uv venv..."
                ${pkgs.uv}/bin/uv venv
              fi
              source .venv/bin/activate
              echo "Syncing dependencies with uv..."
              ${pkgs.uv}/bin/uv sync --extra dev
              echo "Python env is ready!"
            '';
          };
        }
      );
    };
}