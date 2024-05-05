# Installation

This project was developed using the [Poetry](https://python-poetry.org/) package manager and
Python 3.12. To install the Python package and its dependencies, the following bash scripts can
be used:

```bash
pip install poetry
```
**OR**
```bash
sudo apt-get install python3-poetry
```

The second form is necessary if the pip option returns an
"`This environment is externally managed`" error.

```bash
git clone https://github.com/yinchi/histopath-bim-des
cd histopath-bim-des

# if you have obtained a copy of histo.ifc
mkdir -p assets/private/
cp /path/to/histo.ifc assets/private/

# required by erdantic
sudo apt install libgraphviz-dev

# If 3.12 is not the default Python version
poetry venv use /usr/bin/python3/12

poetry install
```
