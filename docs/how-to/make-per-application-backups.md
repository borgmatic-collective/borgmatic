---
title: How to make per-application backups
---
## Multiple backup configurations

You may find yourself wanting to create different backup policies for
different applications on your system. For instance, you may want one backup
configuration for your database data directory, and a different configuration
for your user home directories.

The way to accomplish that is pretty simple: Create multiple separate
configuration files and place each one in a `/etc/borgmatic.d/` directory. For
instance:

```bash
sudo mkdir /etc/borgmatic.d
sudo generate-borgmatic-config --destination /etc/borgmatic.d/app1.yaml
sudo generate-borgmatic-config --destination /etc/borgmatic.d/app2.yaml
```

When you set up multiple configuration files like this, borgmatic will run
each one in turn from a single borgmatic invocation. This includes, by
default, the traditional `/etc/borgmatic/config.yaml` as well.

And if you need even more customizability, you can specify alternate
configuration paths on the command-line with borgmatic's `--config` option.
See `borgmatic --help` for more information.


## Configuration includes

Once you have multiple different configuration files, you might want to share
common configuration options across these files with having to copy and paste
them. To achieve this, you can put fragments of common configuration options
into a file, and then include or inline that file into one or more borgmatic
configuration files.

Let's say that you want to include common retention configuration across all
of your configuration files. You could do that in each configuration file with
the following:

```yaml
location:
   ...

retention:
    !include /etc/borgmatic/common_retention.yaml
```

And then the contents of `common_retention.yaml` could be:

```yaml
keep_hourly: 24
keep_daily: 7
```

To prevent borgmatic from trying to load these configuration fragments by
themselves and complaining that they are not valid configuration files, you
should put them in a directory other than `/etc/borgmatic.d/`. (A subdirectory
is fine.)

Note that this form of include must be a YAML value rather than a key. For
example, this will not work:

```yaml
location:
   ...

# Don't do this. It won't work!
!include /etc/borgmatic/common_retention.yaml
```

But if you do want to merge in a YAML key and its values, keep reading!


## Include merging

If you need to get even fancier and pull in common configuration options while
potentially overriding individual options, you can perform a YAML merge of
included configuration using the YAML `<<` key. For instance, here's an
example of a main configuration file that pulls in two retention options via
an include, and then overrides one of them locally:

```yaml
location:
   ...

retention:
    keep_daily: 5
    <<: !include /etc/borgmatic/common_retention.yaml
```

This is what `common_retention.yaml` might look like:

```yaml
keep_hourly: 24
keep_daily: 7
```

Once this include gets merged in, the resulting configuration would have a
`keep_hourly` value of `24` and an overridden `keep_daily` value of `5`.

When there is a collision of an option between the local file and the merged
include, the local file's option takes precedent. And note that this is a
shallow merge rather than a deep merge, so the merging does not descend into
nested values.

Note that this `<<` include merging syntax is only for merging in mappings
(keys/values). If you'd like to include other types like scalars or lists
directly, please see the section above about standard includes.


## Related documentation

 * [Set up backups with borgmatic](https://torsion.org/borgmatic/docs/how-to/set-up-backups.md)
