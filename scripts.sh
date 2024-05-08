build-docs() {
    pushd `git rev-parse --show-toplevel`
    poetry run sphinx-apidoc -fe -o docs/apidoc/ histopath_bim_des/
    pushd docs
    rm -rf html
    poetry run make html
    cp -r _build/html .
    popd
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

projroot() {
    cd `git rev-parse --show-toplevel`
}

PATH=$PATH:`git rev-parse --show-toplevel`/scripts
