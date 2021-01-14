{ pkgs ? import <nixpkgs> {} }:
  pkgs.mkShell {
    buildInputs = [
      pkgs.python3
      pkgs.python38Packages.scrapy
      pkgs.python38Packages.numpy
    ];
}
