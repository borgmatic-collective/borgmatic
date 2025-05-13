---
title: How to upgrade borgmatic and Borg
eleventyNavigation:
  key: 📦 Upgrade borgmatic/Borg
  parent: How-to guides
  order: 14
---
## Upgrading borgmatic

In general, all you should need to do to upgrade borgmatic if you've
[installed it with
pipx](https://torsion.org/borgmatic/docs/how-to/set-up-backups/#installation)
is to run the following:

```bash
sudo pipx upgrade borgmatic
```

Omit `sudo` if you installed borgmatic as a non-root user. And if you
installed borgmatic *both* as root and as a non-root user, you'll need to
upgrade each installation independently.

If you originally installed borgmatic with `sudo pip3 install --user`, you can
uninstall it first with `sudo pip3 uninstall borgmatic` and then [install it
again with
pipx](https://torsion.org/borgmatic/docs/how-to/set-up-backups/#installation),
which should better isolate borgmatic from your other Python applications.

But if you [installed borgmatic without pipx or
pip3](https://torsion.org/borgmatic/docs/how-to/set-up-backups/#other-ways-to-install),
then your upgrade method may be different.



### Upgrading your configuration

The borgmatic configuration file format is usually backwards-compatible from
release to release without any changes, but you may still want to update your
configuration file when you upgrade to take advantage of new configuration
options or avoid old configuration from eventually becoming unsupported. If
you prefer, you can add new configuration options manually.

If you do want to upgrade your configuration file to include new options, use
the `borgmatic config generate` action with its optional `--source` flag that
takes the path to your original configuration file. If provided with this
path, `borgmatic config generate` merges your original configuration into the
generated configuration file, so you get all the newest options and comments.

Here's an example:

```bash
borgmatic config generate --source config.yaml --destination config-new.yaml
```

<span class="minilink minilink-addedin">Prior to version 1.7.15</span> The
command to generate configuration files was `generate-borgmatic-config`
instead of `borgmatic config generate`.

New options start as commented out, so you can edit the file and decide
whether you want to use each one.

There are a few caveats to this process. First, when generating the new
configuration file, `borgmatic config generate` replaces any comments you've
written in your original configuration file with the newest generated
comments. Second, the script adds back any options you had originally deleted,
although it does so with the options commented out. And finally, any YAML
includes you've used in the source configuration get flattened out into a
single generated file.

As a safety measure, `borgmatic config generate` refuses to modify
configuration files in-place. So it's up to you to review the generated file
and, if desired, replace your original configuration file with it.


### Upgrading from borgmatic 1.0.x

borgmatic changed its configuration file format in version 1.1.0 from
INI-style to YAML. This better supports validation and has a more natural way
to express lists of values. Modern versions of borgmatic no longer include
support for upgrading configuration files this old, but feel free to [file a
ticket](https://torsion.org/borgmatic/#issues) for help with upgrading any old
INI-style configuration files you may have.


### Versioning and breaking changes

To avoid version number bloat, borgmatic doesn't follow traditional semantic
versioning. But here's how borgmatic versioning generally works:

 * Major version bumps (e.g., 1 to 2): Major breaking changes. Configuration
   file formats might change, deprecated features may be removed entirely, etc.
 * Minor version bumps (e.g., 1.8 to 1.9): Medium breaking changes. Depending
   on the features you use, this may be a drop-in replacement. But read the
   release notes to make sure.
 * Patch version bumps (e.g., 1.8.13 to 1.8.14): Minor breaking changes. These
   include, for instance, bug fixes that are technically breaking but may only
   affect a small subset of users.

Each breaking change is prefixed with "BREAKING:" in [borgmatic's release
notes](https://projects.torsion.org/borgmatic-collective/borgmatic/releases),
so there should hopefully be no surprises.


## Upgrading Borg

To upgrade to a new version of Borg, you can generally install a new version
the same way you installed the previous version, paying attention to any
instructions included with each Borg release changelog linked from the
[releases page](https://github.com/borgbackup/borg/releases). Some more major
Borg releases require additional steps that borgmatic can help with.


### Borg 1.2 to 2.0

<span class="minilink minilink-addedin">New in borgmatic version 1.9.0</span>
Upgrading Borg from 1.2 to 2.0 requires manually upgrading your existing Borg
1 repositories before use with Borg or borgmatic. Here's how you can
accomplish that.

Start by upgrading borgmatic as described above to at least version 1.7.0 and
Borg to 2.0. Then, rename your repository in borgmatic's configuration file to
a new repository path. The repository upgrade process does not occur
in-place; you'll create a new repository with a copy of your old repository's
data.

Let's say your original borgmatic repository configuration file looks something
like this:

```yaml
repositories:
    - path: original.borg
```

Change it to a new (not yet created) repository path:

```yaml
repositories:
    - path: upgraded.borg
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> This
option was found in the `location:` section of your configuration.

<span class="minilink minilink-addedin">Prior to version 1.7.10</span> Omit
the `path:` portion of the `repositories` list.

Then, run the `repo-create` action (formerly `init`) to create that new Borg 2
repository:

```bash
borgmatic repo-create --verbosity 1 --encryption repokey-blake2-aes-ocb \
    --source-repository original.borg --repository upgraded.borg
```

This creates an empty repository and doesn't actually transfer any data yet.
The `--source-repository` flag is necessary to reuse key material from your
Borg 1 repository so that the subsequent data transfer can work.

The `--encryption` value above selects the same chunk ID algorithm (`blake2`)
commonly used in Borg 1, thereby making deduplication work across transferred
archives and new archives.

If you get an error about "You must keep the same ID hash" from Borg, that
means the encryption value you specified doesn't correspond to your source
repository's chunk ID algorithm. In that case, try not using `blake2`:

```bash
borgmatic repo-create --verbosity 1 --encryption repokey-aes-ocb \
    --source-repository original.borg --repository upgraded.borg
```

Read about [Borg encryption
modes](https://borgbackup.readthedocs.io/en/latest/usage/repo-create.html)
for more details.

To transfer data from your original Borg 1 repository to your newly created
Borg 2 repository:

```bash
borgmatic transfer --verbosity 1 --upgrader From12To20 --source-repository \
    original.borg --repository upgraded.borg --dry-run
borgmatic transfer --verbosity 1 --upgrader From12To20 --source-repository \
    original.borg --repository upgraded.borg
borgmatic transfer --verbosity 1 --upgrader From12To20 --source-repository \
    original.borg --repository upgraded.borg --dry-run
```

The first command with `--dry-run` tells you what Borg is going to do during
the transfer, the second command actually performs the transfer/upgrade (this
might take a while), and the final command with `--dry-run` again provides
confirmation of success—or tells you if something hasn't been transferred yet.

Note that by omitting the `--upgrader` flag, you can also do archive transfers
between related Borg 2 repositories without upgrading, even down to individual
archives. For more on that functionality, see the [Borg transfer
documentation](https://borgbackup.readthedocs.io/en/2.0.0b16/usage/transfer.html).

That's it! Now you can use your new Borg 2 repository as normal with
borgmatic. If you've got multiple repositories, repeat the above process for
each.
