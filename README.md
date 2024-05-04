# BIM-DES

**Maintainer:** Yin-Chi Chan, Institute for Manufacturing, University of Cambridge

**Authors:**
- Yin-Chi Chan, University of Cambridge (BIM-DES integration, simulation modules)
- Nicola Moretti, University College London (BIM-DES integration)

## Developer Setup

This project uses the [Poetry](https://python-poetry.org/) package manager.
To set up the project on your local computer, run:

```bash
poetry install
```

Other useful Poetry commands include `add`, `remove`, and `run`. As this project is not meant to
be used as a library, the `build` and `publish` commands are not recommended.

## docs.sh

`docs.sh` contains functions for Sphinx documentation. To use these, run the following in `bash`:

```bash
source docs.sh
clean-docs  # reset the /docs directory
build-docs
serve-docs  # defaulting to port 8000
```