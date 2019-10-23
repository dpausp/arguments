#!/usr/bin/env -S nix-build -o docker-image-ekklesia-portal.tar
# Run this file: ./docker.nix
# It creates a docker image archive called docker-image-ekklesia-portal.tar.
# Import into docker with:
# docker load -i docker-image-ekklesia-portal.tar
{ sources ? null }:
let
  serveApp = import ./nix/serve_app.nix {
    inherit sources;
    appConfigFile = "/config.yml";
    listen = "0.0.0.0:8080";
    tmpdir = "/dev/shm";
  };

  deps = import ./nix/deps.nix { inherit sources; };
  inherit (deps) pkgs;
  version = import ./nix/version.nix;
  user = "ekklesia-portal";
  passwd = pkgs.writeTextDir "etc/passwd" ''
    ${user}:x:10:10:${user}:/:/noshell
  '';
in

pkgs.dockerTools.buildLayeredImage {
  name = "ekklesia-portal";
  tag = version;
  contents = [ passwd ];

  config = {
    ExposedPorts = { "8080/tcp" = {}; };
    User = user;
    Entrypoint = "${serveApp}/bin/run";
    Cmd = [ "# runs gunicorn" ];
  };
}
