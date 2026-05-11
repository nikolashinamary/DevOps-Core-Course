{ pkgs }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  copyToRoot = pkgs.buildEnv {
    name = "image-root";
    paths = [ app pkgs.coreutils ];
    pathsToLink = [ "/bin" "/libexec" ];
  };

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
  };

  created = "1970-01-01T00:00:01Z";
}
