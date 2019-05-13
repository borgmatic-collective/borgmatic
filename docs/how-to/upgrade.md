---
title: How to upgrade borgmatic
---
## Upgrading

In general, all you should need to do to upgrade borgmatic is run the
following:

```bash
sudo pip3 install --user --upgrade borgmatic
```

See below about special cases.


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


## Related documentation

 * [Develop on borgmatic](../../docs/how-to/develop-on-borgmatic.md)
