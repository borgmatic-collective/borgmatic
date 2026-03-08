---
title: 📥 How to install borgmatic
eleventyNavigation:
  key: 📥 Install borgmatic
  parent: How-to guides
  order: -1
---

To install borgmatic, first [install
Borg](https://borgbackup.readthedocs.io/en/stable/installation.html), at least
version 1.1. (borgmatic does not install Borg automatically so as to avoid
conflicts with existing Borg installations.)

Then, [install pipx](https://pypa.github.io/pipx/installation/) as the root
user (with `sudo`) to make installing borgmatic easier without impacting other
Python applications on your system. If you have trouble installing pipx with
pip, then you can install a system package instead. E.g. on Ubuntu or Debian,
run:

```bash
sudo apt update
sudo apt install pipx
```

### Root install

If you want to run borgmatic on a schedule with privileged access to your
files, then you should install borgmatic as the root user by running the
following commands:

```bash
sudo pipx ensurepath
sudo pipx install borgmatic
```

Check whether this worked with:

```bash
sudo su -
borgmatic --version
```

If borgmatic is properly installed, that should output your borgmatic version.
And if you'd also like `sudo borgmatic` to work, keep reading!


### Non-root install

If you only want to run borgmatic as a non-root user (without privileged file
access) *or* you want to make `sudo borgmatic` work so borgmatic runs as root,
then install borgmatic as a non-root user by running the following commands as
that user:

```bash
pipx ensurepath
pipx install borgmatic
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
 * [uv tool install](https://docs.astral.sh/uv/)


## Next steps

* [Set up backups](https://torsion.org/borgmatic/how-to/set-up-backups/)
