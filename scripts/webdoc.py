#!/usr/bin/env python

import os, sys
import git

# OPEN URL FROM SPHINX's CONF.PY `intersphinx_mapping`
#
# This script will open the Sphinx documentation for a
# given Python library, if it is defined in the conf.py
# file of a Sphinx project.  If no library is specified,
# the contents of the `intersphinx_mapping` variable is
# shown instead.

def get_git_root(path):
    git_repo = git.Repo(path, search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")
    return git_root

mypath = get_git_root(os.getcwd())


exec(open(f'{mypath}/docs/conf.py', 'r', encoding='utf-8').read())

if len(sys.argv) == 1:
    for k, v in intersphinx_mapping.items():
        print(k, v[0])
    print()

else:
    url = intersphinx_mapping.get(sys.argv[1], None)[0]
    if url:
        print(url)
        os.system(f"xdg-open '{url}' >/dev/null 2>&1")
    else:
        print(f'{sys.argv[1]} not in intersphinx_mapping.')
