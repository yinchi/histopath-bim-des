# BIM-DES

**Maintainer:** Yin-Chi Chan, Institute for Manufacturing, University of Cambridge

**Authors:**
- Yin-Chi Chan, University of Cambridge (BIM-DES integration, simulation modules)
- Nicola Moretti, University College London (BIM-DES integration)

## Developer Setup

**VSCode and WSL2 (for Windows users)**

It is recommended to work on this project using Visual Studio Code with WSL2, which provides a
Linux environment on Windows. See
[this tutorial](https://learn.microsoft.com/en-us/windows/wsl/tutorials/wsl-vscode) on
how to set up VSCode and WSL2.

**Cloning the repository**

```bash
git clone https://github.com/yinchi/histopath-bim-des.git
cd histopath-bim-des

# Open the newly cloned repo in VS Code
code .
```

**Installing the project and its dependencies**

This project uses the [Poetry](https://python-poetry.org/) package manager.
To set up the project on your local computer, run:

```bash
# Installs poetry system-wide 
sudo apt install python3-poetry
# optional
poetry config virtualenvs.in-project true

poetry install
```

Other useful Poetry commands include `add`, `remove`, and `run`. As this project is not meant to
be used as a library, the `build` and `publish` commands are not recommended.

## scripts.sh

`scripts.sh` contains functions for Sphinx documentation. To use these, run the following in `bash`:

```bash
poetry shell

# in the new bash subshell:

source scripts.sh
clean-docs  # reset the /docs directory
build-docs
serve-docs  # defaulting to port 8000

# use CTRL+D to exit to the base shell.
```

`scripts.sh` also provides `projroot()` for quickly changing to the root of the project directory,
as well as adding `script/` to the `PATH` environment variable.

