---
title: How to upgrade borgmatic and Borg
eleventyNavigation:
  key: 📦 Upgrade borgmatic/Borg
  parent: How-to guides
  order: 12
---
## Upgrading borgmatic

In general, all you should need to do to upgrade borgmatic is run the
following:

```bash
sudo pip3 install --user --upgrade borgmatic
```

See below about special cases with old versions of borgmatic. Additionally, if
you installed borgmatic [without using `pip3 install
--user`](https://torsion.org/borgmatic/docs/how-to/set-up-backups/#other-ways-to-install),
then your upgrade process may be different.


### Upgrading your configuration

The borgmatic configuration file format is almost always backwards-compatible
from release to release without any changes, but you may still want to update
your configuration file when you upgrade to take advantage of new
configuration options. This is completely optional. If you prefer, you can add
new configuration options manually.

If you do want to upgrade your configuration file to include new options, use
the `generate-borgmatic-config` script with its optional `--source` flag that
takes the path to your original configuration file. If provided with this
path, `generate-borgmatic-config` merges your original configuration into the
generated configuration file, so you get all the newest options and comments.

Here's an example:

```bash
generate-borgmatic-config --source config.yaml --destination config-new.yaml
```

New options start as commented out, so you can edit the file and decide
whether you want to use each one.

There are a few caveats to this process. First, when generating the new
configuration file, `generate-borgmatic-config` replaces any comments you've
written in your original configuration file with the newest generated
comments. Second, the script adds back any options you had originally deleted,
although it does so with the options commented out. And finally, any YAML
includes you've used in the source configuration get flattened out into a
single generated file.

As a safety measure, `generate-borgmatic-config` refuses to modify
configuration files in-place. So it's up to you to review the generated file
and, if desired, replace your original configuration file with it.


### Upgrading from borgmatic 1.0.x

borgmatic changed its configuration file format in version 1.1.0 from
INI-style to YAML. This better supports validation, and has a more natural way
to express lists of values. To upgrade your existing configuration, first
upgrade to the new version of borgmatic.

As of version 1.1.0, borgmatic no longer supports Python 2. If you were
already running borgmatic with Python 3, then you can upgrade borgmatic
in-place:

```bash
sudo pip3 install --user --upgrade borgmatic
```

But if you were running borgmatic with Python 2, uninstall and reinstall instead:

```bash
sudo pip uninstall borgmatic
sudo pip3 install --user borgmatic
```

The pip binary names for different versions of Python can differ, so the above
commands may need some tweaking to work on your machine.


Once borgmatic is upgraded, run:

```bash
sudo upgrade-borgmatic-config
```

That will generate a new YAML configuration file at /etc/borgmatic/config.yaml
(by default) using the values from both your existing configuration and
excludes files. The new version of borgmatic will consume the YAML
configuration file instead of the old one.


### Upgrading from atticmatic

You can ignore this section if you're not an atticmatic user (the former name
of borgmatic).

borgmatic only supports Borg now and no longer supports Attic. So if you're
an Attic user, consider switching to Borg. See the [Borg upgrade
command](https://borgbackup.readthedocs.io/en/stable/usage.html#borg-upgrade)
for more information. Then, follow the instructions above about setting up
your borgmatic configuration files.

If you were already using Borg with atticmatic, then you can upgrade
from atticmatic to borgmatic by running the following commands:

```bash
sudo pip3 uninstall atticmatic
sudo pip3 install --user borgmatic
```

That's it! borgmatic will continue using your /etc/borgmatic configuration
files.


## Upgrading Borg

To upgrade to a new version of Borg, you can generally install a new version
the same way you installed the previous version, paying attention to any
instructions included with each Borg release changelog linked from the
[releases page](https://github.com/borgbackup/borg/releases). Some more major
Borg releases require additional steps that borgmatic can help with.


### Borg 1.2 to 2.0

<span class="minilink minilink-addedin">New in borgmatic version 1.7.0</span>
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
location:
    repositories:
        - original.borg
```

Change it to a new (not yet created) repository path:

```yaml
location:
    repositories:
        - upgraded.borg
```

Then, run the `rcreate` action (formerly `init`) to create that new Borg 2
repository:

```bash
borgmatic rcreate --verbosity 1 --encryption repokey-blake2-aes-ocb \
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
borgmatic rcreate --verbosity 1 --encryption repokey-aes-ocb \
    --source-repository original.borg --repository upgraded.borg
```

Read about [Borg encryption
modes](https://borgbackup.readthedocs.io/en/2.0.0b5/usage/rcreate.html#encryption-mode-tldr)
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
documentation](https://borgbackup.readthedocs.io/en/2.0.0b5/usage/transfer.html).

That's it! Now you can use your new Borg 2 repository as normal with
borgmatic. If you've got multiple repositories, repeat the above process for
each.
