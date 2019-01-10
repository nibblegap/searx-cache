#!/bin/sh

BASE_DIR="$(dirname -- "`readlink -f -- "$0"`")"

cd -- "$BASE_DIR"
set -e

# subshell
PYTHONPATH="$BASE_DIR"
SEARX_DIR="$BASE_DIR/searx"
ACTION="$1"


#
# Python
#

update_packages() {
    pip3 install --upgrade pip
    pip3 install --upgrade setuptools
    pip3 install -r "$BASE_DIR/requirements.txt"
}

update_dev_packages() {
    update_packages
    pip3 install -r "$BASE_DIR/requirements-dev.txt"
}

locales() {
    pybabel compile -d "$SEARX_DIR/translations"
}

pep8_check() {
    echo '[!] Running pep8 check'
    # ignored rules:
    #  E402 module level import not at top of file
    #  W503 line break before binary operator
    pep8 --exclude=searx/static --max-line-length=120 --ignore "E402,W503" "$SEARX_DIR" "$BASE_DIR/tests"
}

unit_tests() {
    echo '[!] Running unit tests'
    PYTHONPATH="$BASE_DIR" pytest --cov=searx --disable-pytest-warnings "$BASE_DIR/tests/unit"
}

py_test_coverage() {
    echo '[!] Running python test coverage'
    PYTHONPATH="`pwd`" python3 -m nose2 -C --log-capture --with-coverage --coverage "$SEARX_DIR" -s "$BASE_DIR/tests/unit" \
    && coverage report \
    && coverage html
}

tests() {
    set -e
    pep8_check
    unit_tests
    set +e
}


#
# Web
#

npm_path_setup() {
    which npm &>/dev/null || whereis npm &>/dev/null || (printf 'Error: npm is not found\n'; exit 1)
    export PATH="$(npm bin)":$PATH
}

npm_packages() {
    npm_path_setup

    echo '[!] install NPM packages'
    cd -- "$BASE_DIR"
    npm install less@2.7 less-plugin-clean-css grunt-cli

    echo '[!] install NPM packages for oscar theme'
    cd -- "$BASE_DIR/searx/static/themes/oscar"
    npm install

    echo '[!] install NPM packages for simple theme'
    cd -- "$BASE_DIR/searx/static/themes/simple"
    npm install
}

build_style() {
    npm_path_setup

    lessc --clean-css="--s1 --advanced --compatibility=ie9" "$BASE_DIR/searx/static/$1" "$BASE_DIR/searx/static/$2"
}

styles() {
    npm_path_setup

    echo '[!] Building legacy style'
    build_style themes/legacy/less/style.less themes/legacy/css/style.css
    build_style themes/legacy/less/style-rtl.less themes/legacy/css/style-rtl.css
    echo '[!] Building courgette style'
    build_style themes/courgette/less/style.less themes/courgette/css/style.css
    build_style themes/courgette/less/style-rtl.less themes/courgette/css/style-rtl.css
    echo '[!] Building pix-art style'
    build_style themes/pix-art/less/style.less themes/pix-art/css/style.css
    echo '[!] Building bootstrap style'
    build_style less/bootstrap/bootstrap.less css/bootstrap.min.css
}

grunt_build() {
    npm_path_setup
    echo '[!] Grunt build : oscar theme'
    grunt --gruntfile "$SEARX_DIR/static/themes/oscar/gruntfile.js"
    echo '[!] Grunt build : simple theme'
    grunt --gruntfile "$SEARX_DIR/static/themes/simple/gruntfile.js"
}

#
# Help
#

help() {
    [ -z "$1" ] || printf 'Error: %s\n' "$1"
    echo "Searx manage.sh help

Commands
========
    help                 - This text

    Build requirements
    ------------------
    update_packages      - Check & update production dependency changes
    update_dev_packages  - Check & update development and production dependency changes
    install_geckodriver  - Download & install geckodriver if not already installed (required for robot_tests)
    npm_packages         - Download & install npm dependencies (source manage.sh to update the PATH)

    Build
    -----
    locales              - Compile locales
    styles               - Build less files
    grunt_build          - Build files for themes

    Tests
    -----
    unit_tests           - Run unit tests
    pep8_check           - Pep8 validation
    robot_tests          - Run selenium tests
    tests                - Run all python tests (pep8, unit, robot_tests)
    py_test_coverage     - Unit test coverage
"
}

[ "$(command -V "$ACTION" | grep ' function$')" = "" ] \
    && help "action not found" \
    || "$ACTION" "$2"
