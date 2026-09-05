{
  description = "A quiet, native PDF reader & warm paper styler for Linux, Windows & macOS";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;
      in
      rec {
        packages.paperizer = python.pkgs.buildPythonApplication rec {
          pname = "paperizer";
          version = "0.1.1";
          format = "pyproject";

          src = ./.;

          nativeBuildInputs = with python.pkgs; [
            hatchling
          ];

          propagatedBuildInputs = with python.pkgs; [
            pyside6
            pikepdf
            pymupdf
          ];

          dontWrapQtApps = false;

          meta = with pkgs.lib; {
            description = "Quiet native PDF reader and warm paper styler";
            homepage = "https://github.com/Refayatul/paperizer";
            license = licenses.mit;
            mainProgram = "paperizer";
          };
        };

        packages.default = packages.paperizer;

        apps.paperizer = flake-utils.lib.mkApp {
          drv = packages.paperizer;
        };
        apps.default = apps.paperizer;

        devShells.default = pkgs.mkShell {
          buildInputs = [
            python
            python.pkgs.pyside6
            python.pkgs.pikepdf
            python.pkgs.pymupdf
            python.pkgs.pytest
            python.pkgs.hatchling
          ];
        };
      });
}
