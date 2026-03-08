---
title: 📥 How to install borgmatic
eleventyNavigation:
  key: 📥 Install borgmatic
  parent: How-to guides
  order: -1
---


### Prerequisites

Before installing borgmatic, first [install
Borg](https://borgbackup.readthedocs.io/en/stable/installation.html), at least
version 1.1. (borgmatic does not install Borg automatically so as to avoid
conflicts with existing Borg installations.)

Then, [install uv](https://docs.astral.sh/uv/getting-started/installation/) as
the root user (with `sudo`) to make installing borgmatic easier without
impacting other Python applications on your system. For Debian, there is a
[third-party package for
uv](https://dario.griffo.io/posts/how-to-install-uv-debian/). On Ubuntu, there
is a [snap package](https://snapcraft.io/install/astral-uv/ubuntu). On Arch, you
can just install the `python-uv` package.


### Root install

If you want borgmatic to run with privileged access so it can backup your system
files, then install borgmatic as the root user by running the following
commands:

```bash
sudo uv tool update-shell
sudo uv tool install borgmatic
```

Check whether this worked with:

```bash
sudo su -
borgmatic --version
```

If borgmatic is properly installed, that should output your borgmatic version.
And if you'd also like `sudo borgmatic` to work as well, keep reading!


### Non-root install

If you only want to run borgmatic as a non-root user (without privileged file
access) *or* you want to make `sudo borgmatic` work so borgmatic runs as root,
then install borgmatic as a non-root user by running the following commands as
that user:

```bash
uv tool update-shell
uv tool install borgmatic
```

This should work even if you've also installed borgmatic as the root user.

Check whether this worked with:

```bash
borgmatic --version
```

If borgmatic is properly installed, that should output your borgmatic version.
You can also try `sudo borgmatic --version` if you intend to run borgmatic
with `sudo`. If that doesn't work, you may need to update your [sudoers
`secure_path` option](https://wiki.archlinux.org/title/Sudo).


### Other ways to install

Besides the approaches described above, there are several other options for
installing borgmatic:

#### <span data-pagefind-weight="7.0">Docker / Podman</span>

 * [container image with scheduled backups](https://github.com/borgmatic-collective/docker-borgmatic) (+ Docker Compose files)
 * [container image with multi-arch and Docker CLI support](https://github.com/modem7/docker-borgmatic)

#### Operating system packages

 * [Debian](https://tracker.debian.org/pkg/borgmatic)
 * [Ubuntu](https://launchpad.net/ubuntu/+source/borgmatic)
 * [Fedora](https://bodhi.fedoraproject.org/updates/?search=borgmatic)
 * [Gentoo](https://packages.gentoo.org/packages/app-backup/borgmatic)
 * [Arch Linux](https://archlinux.org/packages/extra/any/borgmatic/)
 * [Alpine Linux](https://pkgs.alpinelinux.org/packages?name=borgmatic)
 * [OpenBSD](https://openports.pl/path/sysutils/borgmatic)
 * [openSUSE](https://software.opensuse.org/package/borgmatic)
 * [macOS (via Homebrew)](https://formulae.brew.sh/formula/borgmatic)
 * [macOS (via MacPorts)](https://ports.macports.org/port/borgmatic/)
 * [NixOS](https://search.nixos.org/packages?channel=unstable&show=borgmatic&query=borgmatic)

#### Etc.

 * [Ansible role](https://github.com/borgbase/ansible-role-borgbackup)
 * [pipx](https://pipx.pypa.io/stable/)


## Next steps

* [Set up backups](https://torsion.org/borgmatic/how-to/set-up-backups/)
