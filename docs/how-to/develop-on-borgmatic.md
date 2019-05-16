---
title: How to develop on borgmatic
---
## Source code

To get set up to hack on borgmatic, first clone master via HTTPS or SSH:

```bash
git clone https://projects.torsion.org/witten/borgmatic.git
```

Or:

```bash
git clone ssh://git@projects.torsion.org:3022/witten/borgmatic.git
```

Then, install borgmatic
"[editable](https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs)"
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
with Borg for a few representative scenarios. These tests don't run by default
because they're relatively slow and depend on Borg. If you would like to run
them:

```bash
tox -e end-to-end
```

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
[build.torsion.org](https://build.torsion.org/witten/borgmatic), and they're
also linked from the commits list on each pull request.

## Related documentation

 * [Inspect your backups](../../docs/how-to/inspect-your-backups.md)
