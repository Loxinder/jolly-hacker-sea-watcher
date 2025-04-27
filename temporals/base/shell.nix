# shell.nix
# Provides Python from Nixpkgs and automatically sets up/activates a local Python venv.
# Use this when you need specific package versions via pip or packages not available in nixpkgs.

{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/nixos-23.11.tar.gz") {} }:
# Fetches Nixpkgs version 23.11 for reproducibility.
# Update URL and sha256 for a different Nixpkgs version if needed.
# Verify sha256 using: nix-prefetch-url --unpack <URL>
# Example sha256 for 23.11: sha256 = "sha256:1c5nmfb381gpjn8g7p794jm8ccjixb8c7x457f9hy1j54h8z9y6g"; # Verify this hash!

let
  # Specify the desired Python version (must meet 3.9+)
  # Make sure this version exists in your chosen nixpkgs revision
  python = pkgs.python311; # Using Python 3.11 as an example

in
pkgs.mkShell {
  name = "python-venv-shell";

  # Packages needed in the Nix environment:
  # - Just Python itself (which includes the 'venv' module).
  # - Add other system-level build dependencies (like gcc, pkg-config, openssl.dev, zlib)
  #   here if 'pip install' fails because it needs to compile C extensions.
  buildInputs = [
    python
    pkgs.temporal-cli
  ];

  # Shell hook to automatically create and activate the venv
  shellHook = ''
    # Define the virtual environment directory name
    VENV_DIR=".venv"

    # Clear any inherited prompt command that might interfere with venv's prompt modification
    PROMPT_COMMAND=""

    # Set environment variables to ensure venv uses UTF-8 locale, preventing potential issues
    export LANG=en_US.UTF-8
    export LC_ALL=en_US.UTF-8

    echo "------------------------------------------------------------"
    echo " Setting up Python Virtual Environment via Nix Shell...     "
    echo "------------------------------------------------------------"

    # Check if the venv directory exists. If not, create it using the Python from Nixpkgs.
    if [ ! -d "$VENV_DIR" ]; then
      echo ">>> Creating Python virtual environment in '$VENV_DIR' using system Python $(python --version)..."
      # Use the specific interpreter path from the Nix store for reliability
      ${python.interpreter} -m venv "$VENV_DIR"
      echo ">>> Virtual environment created successfully."
    else
      echo ">>> Re-using existing virtual environment found in '$VENV_DIR'."
    fi

    # Activate the virtual environment.
    # The 'source' command executes the activation script in the current shell context.
    echo ">>> Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    # Optional: Uncomment the following lines to automatically install/update
    # dependencies from requirements.txt every time you enter the nix-shell.
    # Can be slow if requirements are large or change often.
    # -------------------------------------------------------------------
    echo ">>> Ensuring dependencies from requirements.txt are installed..."
    pip install -r requirements.txt
    echo ">>> Dependency check/installation complete."
    # -------------------------------------------------------------------

    echo ""
    echo "------------------------------------------------------------"
    echo " Nix Shell Ready - Python Virtual Environment Activated!    "
    echo "------------------------------------------------------------"
    echo "Python interpreter now points to: $(which python)"
    echo "Python version in venv:         $(python --version)"
    echo "Pip location:                   $(which pip)"
    echo ""
    echo ">>> You can now manage packages using pip inside this shell:"
    echo "    pip install -r requirements.txt"
    echo "    pip install <some_other_package>"
    echo "    pip freeze"
    echo ""
    echo ">>> Run your Python application scripts."
    echo ">>> Type 'deactivate' to manually exit the venv, or just exit the nix-shell."
    echo "------------------------------------------------------------"

    # Unset SOURCE_DATE_EPOCH to prevent potential issues with some build tools
    unset SOURCE_DATE_EPOCH
  '';
}