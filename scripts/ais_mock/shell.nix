# shell.nix
#
# Use this file to create a development environment for the AIS Data API project.
# To activate the environment, run `nix-shell` in the directory containing this file.

# Import the Nix Packages collection (nixpkgs).
# '<nixpkgs>' refers to the channel or pinned version of nixpkgs configured in your system.
let
  pkgs = import <nixpkgs> {};

  # Specify the desired Python version. You can change this, e.g., to pkgs.python310
  pythonVersion = pkgs.python311;

  # Define the required Python packages
  pythonPackages = pythonVersion.withPackages (ps: [
    ps.pandas       # For data manipulation (reading CSV, DataFrame operations)
    ps.numpy        # For numerical operations (Haversine calculation)
    ps.fastapi      # The web framework used for the API
    ps.uvicorn      # ASGI server to run FastAPI (with standard features)
    # Add any other Python dependencies here if needed
  ]);

in
# Create the development shell environment
pkgs.mkShell {
  # Name for the shell (optional, cosmetic)
  name = "ais-api-dev-env";

  # List of packages to include in the environment's PATH
  buildInputs = [
    pythonPackages  # This includes Python itself and the specified packages
    # Add other system dependencies here if required (e.g., git, specific compilers)
  ];

  # Optional: Set environment variables within the shell
  # shellHook = ''
  #   export MY_VARIABLE="some_value"
  #   echo "Entered AIS API development environment."
  # '';
}
