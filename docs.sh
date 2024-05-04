build-docs() {
    pushd `git rev-parse --show-toplevel`
    poetry run sphinx-apidoc -fe -o docs/apidoc/ histopath_bim_des/
    cd docs
    poetry run make html
    popd
}

clean-docs() {
    pushd `git rev-parse --show-toplevel`
    cd docs
    poetry run make clean
    popd
}

serve-docs() {
    pushd `git rev-parse --show-toplevel`
    python -m http.server --directory docs/_build/html/
    popd
}
