---
title: How to develop on borgmatic
eleventyNavigation:
  key: 🏗️ Develop on borgmatic
  parent: How-to guides
  order: 15
---
To get set up to develop on borgmatic, first [`install
uv`](https://docs.astral.sh/uv/) to make managing your borgmatic environment
easier without impacting other Python applications on your system.

Then, clone borgmatic via HTTPS or SSH:

```bash
git clone https://projects.torsion.org/borgmatic-collective/borgmatic.git
```

Or:

```bash
git clone ssh://git@projects.torsion.org:3022/borgmatic-collective/borgmatic.git
```

Finally, install borgmatic
"[editable](https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs)"
so that you can run borgmatic actions during development to make sure your
changes work:

```bash
cd borgmatic
uv tool update-shell
uv tool install --editable .
```

Or to work on the [Apprise
hook](https://torsion.org/borgmatic/how-to/monitor-your-backups/#apprise-hook),
change that last line to:

```bash
uv tool install --editable .[Apprise]
```

To get oriented with the borgmatic source code, have a look at the [source
code reference](https://torsion.org/borgmatic/reference/source-code/).


### Source packages

Each [borgmatic
release](https://projects.torsion.org/borgmatic-collective/borgmatic/releases)
also has source packages available. These include automated tests and serve as
a good starting point for creating third-party borgmatic packages.


## Automated tests

Assuming you've cloned the borgmatic source code as described above and you're
in the `borgmatic/` working copy, install [tox](https://tox.wiki/) and
[tox-uv](https://github.com/tox-dev/tox-uv) using uv, which are used for setting
up testing environments:

```bash
uv tool install tox --with tox-uv
```

Also install [Ruff](https://docs.astral.sh/ruff/), which borgmatic uses for code
linting and formatting:

```bash
uv tool install ruff
```

Finally, to actually run tests, run tox from inside the borgmatic source
directory:

```bash
tox
```

That runs tests against all supported versions of Python, which takes a while.
So if you'd only like to run tests against a single version of Python, e.g.
Python 3.13:

```bash
tox -e py313
```


### Code style

If when running tests, you get an error from Ruff's linter about files that
don't meet linting requirements, you can ask Ruff to attempt to fix them for you
via the following:

```bash
tox -e lint-fix
```

And if you get an error from the Ruff's code formatter about files that would be
reformatted, you can ask Ruff to format them for you:

```bash
tox -e format
```

Similarly, if you get errors about spelling mistakes in source code, you can
ask [codespell](https://github.com/codespell-project/codespell) to correct
them:

```bash
tox -e spell
```

See the [code style
documentation](https://torsion.org/borgmatic/reference/source-code/#code-style)
for more specifics about borgmatic's own code style.


### End-to-end tests

borgmatic additionally includes some end-to-end tests that integration test
with Borg and supported databases for a few representative scenarios. These
tests don't run by default when running `tox`, because they're relatively slow
and depend on containers for runtime dependencies. These tests do run on the
continuous integration (CI) server, and running them on your developer machine
is the closest thing to dev-CI parity.

If you would like to run the end-to-end tests, first install Docker (or
Podman; see below) and [Docker
Compose](https://docs.docker.com/compose/install/). Then run:

```bash
scripts/run-end-to-end-tests
```

This script assumes you have permission to run `docker`. If you don't, then
you may need to run with `sudo`.


#### Podman

borgmatic's end-to-end tests optionally support using
[rootless](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md)
[Podman](https://podman.io/) instead of Docker.

Setting up Podman is outside the scope of this documentation, but here are
some key points to double-check:

 * Install Podman and your desired networking support.
 * Configure `/etc/subuid` and `/etc/subgid` to map users/groups for the
   non-root user who will run tests.
 * Create a non-root Podman socket for that user:
   ```bash
   systemctl --user enable --now podman.socket
   systemctl --user start --now podman.socket
   ```

Then you'll be able to run end-to-end tests as per normal, and the test script
will automatically use your non-root Podman socket instead of a Docker socket.


## Continuous integration

Each commit to
[main](https://projects.torsion.org/borgmatic-collective/borgmatic/branches)
triggers [a continuous integration
build](https://projects.torsion.org/borgmatic-collective/borgmatic/actions)
which runs the test suite and updates
[documentation](https://torsion.org/borgmatic/). These builds are also linked
from the [commits for the main
branch](https://projects.torsion.org/borgmatic-collective/borgmatic/commits/branch/main).


## Documentation development

Updates to borgmatic's documentation are welcome. It's formatted in Markdown
and located in the `docs/` directory in borgmatic's source, plus the
`README.md` file at the root.

To build and view a copy of the documentation with your local changes, run the
following from the root of borgmatic's source code:

```bash
scripts/dev-docs
```

This requires Docker (or Podman; see below) to be installed on your system.
This script assumes you have permission to run `docker`. If you don't, then
you may need to run with `sudo`.

After you run the script, you can point your web browser at
http://localhost:8080/borgmatic/ to view the documentation with your changes.

To close the documentation server, ctrl-C the script. Note that it does not
currently auto-reload, so you'll need to stop it and re-run it for any
additional documentation changes to take effect.


#### Podman

borgmatic's developer build for documentation optionally supports using
[rootless](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md)
[Podman](https://podman.io/) instead of Docker.

Setting up Podman is outside the scope of this documentation. But once you
install and configure Podman, then `scripts/dev-docs` should automatically use
Podman instead of Docker.
