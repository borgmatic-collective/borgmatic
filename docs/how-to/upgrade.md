---
title: How to upgrade borgmatic
eleventyNavigation:
  key: 📦 Upgrade borgmatic
  parent: How-to guides
  order: 12
---
## Upgrading

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
