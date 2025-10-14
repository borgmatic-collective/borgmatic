---
title: How to make per-application backups
eleventyNavigation:
  key: 🗂️ Make per-application backups
  parent: How-to guides
  order: 1
---
You may find yourself wanting to create different backup policies for
different applications on your system or even for different backup
repositories. For instance, you might want one backup configuration for your
database data directory and a different configuration for your user home
directories. Or one backup configuration for your local backups with a
different configuration for your remote repository.

The way to accomplish that is pretty simple: Create multiple separate
configuration files and place each one in a `/etc/borgmatic.d/` directory. For
instance, for applications:

```bash
sudo mkdir /etc/borgmatic.d
sudo borgmatic config generate --destination /etc/borgmatic.d/app1.yaml
sudo borgmatic config generate --destination /etc/borgmatic.d/app2.yaml
```

Or, for repositories:

```bash
sudo mkdir /etc/borgmatic.d
sudo borgmatic config generate --destination /etc/borgmatic.d/repo1.yaml
sudo borgmatic config generate --destination /etc/borgmatic.d/repo2.yaml
```

<span class="minilink minilink-addedin">Prior to version 1.7.15</span> The
command to generate configuration files was `generate-borgmatic-config`
instead of `borgmatic config generate`.

When you set up multiple configuration files like this, borgmatic will run
each one in turn from a single borgmatic invocation. This includes, by
default, the traditional `/etc/borgmatic/config.yaml` as well.

Each configuration file is interpreted independently, as if you ran borgmatic
for each configuration file one at a time. In other words, borgmatic does not
perform any merging of configuration files by default. If you'd like borgmatic
to merge your configuration files, for instance to avoid duplication of
settings, see below about configuration includes.

Additionally, the `~/.config/borgmatic.d/` directory works the same way as
`/etc/borgmatic.d`.

If you need even more customizability, you can specify alternate configuration
paths on the command-line with borgmatic's `--config` flag. (See the
[command-line
documentation](https://torsion.org/borgmatic/reference/command-line/) for more
information.) For instance, if you want to schedule your various borgmatic
backups to run at different times, you'll need multiple entries in your
[scheduling software of
choice](https://torsion.org/borgmatic/how-to/set-up-backups/#autopilot), each
entry using borgmatic's `--config` flag instead of relying on
`/etc/borgmatic.d`.


<a id="archive-naming"></a>
<a id="configuration-includes"></a>
<a id="configuration-overrides"></a>
<a id="constant-interpolation"></a>

## Related features

Once you've got multiple configuration files, there are a few other borgmatic
features that you might find handy:

 * Use different archive naming schemes in each configuration file with the
   [archive name
   format](https://torsion.org/borgmatic/reference/configuration/archive-name-format/)
   feature.
 * Share common options across configuration files with
   [includes](https://torsion.org/borgmatic/reference/configuration/includes/).
 * Override configuration file options from the command-line with
   [overrides](https://torsion.org/borgmatic/reference/command-line/overrides/).
 * Also check out the
   [constants](https://torsion.org/borgmatic/reference/configuration/constants/)
   feature for defining custom per-configuration-file constants.
