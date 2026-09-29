---
title: 🗃️ Repositories
eleventyNavigation:
  key: 🗃️ Repositories
  parent: ⚙️  Configuration
---

Borg repositories are where your backups get stored. You can define them in
borgmatic's configuration via the `repositories` option, something like:

```yaml
repositories:
    - path: /path/to/first.borg
      label: first
    - path: /path/to/second.borg
      label: second
```

Each repository has a `path` and an optional `label`. The [Borg repository URLs
documentation](https://borgbackup.readthedocs.io/en/stable/usage/general.html#repository-urls)
has examples of valid repositories paths, but see below for some
borgmatic-specific examples.

The `label` shows up in [logged
messages](https://torsion.org/borgmatic/reference/command-line/logging/) about
the repository and also serves as a way to refer to the repository via
the `--repository` flag on the command-line for supported
[actions](https://torsion.org/borgmatic/reference/command-line/actions/).

When you run borgmatic's [`create`
action](https://torsion.org/borgmatic/reference/command-line/actions/create/),
it invokes Borg once for each configured repository in sequence. (So, not in
parallel.) That means—in each repository—borgmatic creates a single new backup
archive containing all of your [source
directories](https://torsion.org/borgmatic/reference/configuration/patterns-and-excludes/).


## Repository-specific configuration

<span class="minilink minilink-addedin">New in version 2.1.10</span> If you want
certain borgmatic [configuration
options](https://torsion.org/borgmatic/reference/configuration/) to apply only
to particular repositories (and you don't want to mess with [separate
configuration
files](https://torsion.org/borgmatic/how-to/make-per-application-backups/)), you
can specify many top-level configuration options directly under particular
repositories. For example:

```yaml
repositories:
    - path: /path/to/repo1.borg
      local_path: borg1
      remote_path: borg1
    - path: /path/to/repo2.borg
      local_path: borg2
      remote_path: borg2
```

This example demonstrates how you can specify options like `local_path` and
`remote_path` to be repository specific, even though they are typically
top-level configuration options that apply for all repositories.

Under the hood, borgmatic merges these values into the top-level configuration
when determining the configuration to use for a particular
repository—overwriting any top-level configuration options that may already
exist (but just for that repository). This is performed as a shallow merge, so
use [includes](https://torsion.org/borgmatic/reference/configuration/includes/)
and multiple configuration files if you need deep merging.

Note that this feature doesn't make sense for every configuration option. For
instance, borgmatic consumes options like `verbosity` before any per-repository
logic, so in that case per-repository `verbosity` values get silently ignored.


## SSH

Backing up to a remote server via
[SSH](https://en.wikipedia.org/wiki/Secure_Shell) looks like:

```yaml
repositories:
    - path: ssh://user@host:port/./absolute/path/to/repo
```

Or relative to the remote user's home directory:

```yaml
repositories:
    - path: ssh://user@host:port/~/relative/path/to/repo
```

This assumes that you've already configured SSH access (e.g. public keys, known
hosts, authorized hosts, etc.) outside of borgmatic and that Borg is installed
on the server.

<span class="minilink minilink-addedin">With Borg version 2.x</span>The SSH
syntax is a little different:

```yaml
repositories:
    - path: ssh://user@host:port//absolute/path/to/repo
```

Or relative to the remote user's home directory:


```yaml
repositories:
    - path: ssh://user@host:port/relative/path/to/repo
```

Also see the [`ssh_command` configuration
option](https://torsion.org/borgmatic/reference/configuration/) for overriding
the path to the SSH binary or passing it custom flags. For example:

```yaml
ssh_command: ssh -i /path/to/private/key
```


### SFTP

[SFTP](https://en.wikipedia.org/wiki/SSH_File_Transfer_Protocol) repositories
work just like SSH repositories, but with `sftp://` substituted for `ssh://`.


## Rclone

<span class="minilink minilink-addedin">New in Borg version 2.x</span> If you're
using Borg 2, you can backup to repositories via [Rclone](https://rclone.org/),
which supports a large number of [cloud
providers](https://rclone.org/#providers). This means that Borg, via Rclone,
backs up directly to a cloud provider without having to create an intermediate
repository.

The borgmatic configuration for Rclone looks like:

```yaml
repositories:
    - path: rclone:remote:path
```

Note the lack of "`//`" after `rclone:`.

This configuration assumes that you've already [configured a corresponding
Rclone remote](https://rclone.org/docs/).


## S3 / B2

<span class="minilink minilink-addedin">New in Borg version 2.x</span> Borg 2
supports storing repositories directly on [Amazon
S3](https://aws.amazon.com/s3/), [Backblaze
B2](https://www.backblaze.com/cloud-storage), or an S3-alike service, even
without the use of Rclone or an intermediate repository. The configuration for
that might look like one of the following:

```yaml
repositories:
    - path: s3:access_key_id:access_key_secret@/bucket/path 
    - path: b2:access_key_id:access_key_secret@schema://hostname:port/bucket/path 
```

Note the lack of "`//`" after `s3:` or `b2:`.

<span class="elv-info-warn">When selecting your cloud hosting provider, be aware
that Amazon in particular has [financially
supported](https://en.wikipedia.org/wiki/White_House_State_Ballroom) the Trump
regime and [sold tech
services](https://progressive.international/wire/2025-08-26-un-calls-out-google-and-amazon-for-abetting-gaza-genocide/en/)
to Israel used directly in their genocide in Gaza. Additionally, U.S.
Immigration and Customs Enforcement (ICE) is [powered by
Amazon](https://medium.com/@noazureforapartheid/microsoft-powers-ice-why-doesnt-microsoft-want-to-talk-about-its-contracts-with-immigration-and-bc04fae8d43b).</span>


## Related documentation

 * [How to make backups redundant](https://torsion.org/borgmatic/how-to/make-backups-redundant/)
 * [How to provide your passwords](https://torsion.org/borgmatic/how-to/provide-your-passwords/)
