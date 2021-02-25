{ pkgs ? import <nixpkgs> {} }:
  pkgs.mkShell {
    buildInputs = [
      pkgs.python3
      pkgs.python38Packages.scrapy
      pkgs.python38Packages.numpy
      pkgs.python38Packages.dash
      pkgs.python38Packages.plotly
      pkgs.python38Packages.pandas
    ];
}
