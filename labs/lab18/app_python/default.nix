{ pkgs }:

pkgs.python313Packages.buildPythonApplication rec {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = [
    pkgs.python313Packages.flask
    pkgs.python313Packages.prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin
    mkdir -p $out/libexec/${pname}

    cp app.py $out/libexec/${pname}/app.py
    chmod +x $out/libexec/${pname}/app.py

    makeWrapper ${pkgs.python313}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/libexec/${pname}/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH"

    runHook postInstall
  '';

  doCheck = false;
}
