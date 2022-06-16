---
title: How to develop on borgmatic
eleventyNavigation:
  key: 🏗️ Develop on borgmatic
  parent: How-to guides
  order: 13
---
## Source code

To get set up to hack on borgmatic, first clone master via HTTPS or SSH:

```bash
git clone https://projects.torsion.org/borgmatic-collective/borgmatic.git
```

Or:

```bash
git clone ssh://git@projects.torsion.org:3022/borgmatic-collective/borgmatic.git
```

Then, install borgmatic
"[editable](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs)"
so that you can run borgmatic commands while you're hacking on them to
make sure your changes work.

```bash
cd borgmatic/
pip3 install --editable --user .
```

Note that this will typically install the borgmatic commands into
`~/.local/bin`, which may or may not be on your PATH. There are other ways to
install borgmatic editable as well, for instance into the system Python
install (so without `--user`, as root), or even into a
[virtualenv](https://virtualenv.pypa.io/en/stable/). How or where you install
borgmatic is up to you, but generally an editable install makes development
and testing easier.


## Automated tests

Assuming you've cloned the borgmatic source code as described above, and
you're in the `borgmatic/` working copy, install tox, which is used for
setting up testing environments:

```bash
pip3 install --user tox
```

Finally, to actually run tests, run:

```bash
cd borgmatic
tox
```

### Code formatting

If when running tests, you get an error from the
[Black](https://black.readthedocs.io/en/stable/) code formatter about files
that would be reformatted, you can ask Black to format them for you via the
following:

```bash
tox -e black
```

And if you get a complaint from the
[isort](https://github.com/timothycrosley/isort) Python import orderer, you
can ask isort to order your imports for you:

```bash
tox -e isort
```

### End-to-end tests

borgmatic additionally includes some end-to-end tests that integration test
with Borg and supported databases for a few representative scenarios. These
tests don't run by default when running `tox`, because they're relatively slow
and depend on Docker containers for runtime dependencies. These tests tests do
run on the continuous integration (CI) server, and running them on your
developer machine is the closest thing to CI test parity.

If you would like to run the full test suite, first install Docker and [Docker
Compose](https://docs.docker.com/compose/install/). Then run:

```bash
scripts/run-full-dev-tests
```

Note that this scripts assumes you have permission to run Docker. If you
don't, then you may need to run with `sudo`.

## Code style

Start with [PEP 8](https://www.python.org/dev/peps/pep-0008/). But then, apply
the following deviations from it:

 * For strings, prefer single quotes over double quotes.
 * Limit all lines to a maximum of 100 characters.
 * Use trailing commas within multiline values or argument lists.
 * For multiline constructs, put opening and closing delimeters on lines
   separate from their contents.
 * Within multiline constructs, use standard four-space indentation. Don't align
   indentation with an opening delimeter.

borgmatic code uses the [Black](https://black.readthedocs.io/en/stable/) code
formatter, the [Flake8](http://flake8.pycqa.org/en/latest/) code checker, and
the [isort](https://github.com/timothycrosley/isort) import orderer, so
certain code style requirements will be enforced when running automated tests.
See the Black, Flake8, and isort documentation for more information.

## Continuous integration

Each pull request triggers a continuous integration build which runs the test
suite. You can view these builds on
[build.torsion.org](https://build.torsion.org/borgmatic-collective/borgmatic), and they're
also linked from the commits list on each pull request.

## Documentation development

Updates to borgmatic's documentation are welcome. It's formatted in Markdown
and located in the `docs/` directory in borgmatic's source, plus the
`README.md` file at the root.

To build and view a copy of the documentation with your local changes, run the
following from the root of borgmatic's source code:

```bash
sudo scripts/dev-docs
```

This requires Docker to be installed on your system. You may not need to use
sudo if your non-root user has permissions to run Docker.

After you run the script, you can point your web browser at
http://localhost:8080 to view the documentation with your changes.

To close the documentation server, ctrl-C the script. Note that it does not
currently auto-reload, so you'll need to stop it and re-run it for any
additional documentation changes to take effect.
