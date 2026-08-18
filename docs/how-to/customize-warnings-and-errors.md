---
title: 💥 How to customize warnings and errors
eleventyNavigation:
  key: 💥 Customize warnings/errors
  parent: How-to guides
  order: 13
---

After Borg runs, it indicates whether it succeeded via its exit code, a numeric
ID indicating success, warning, or error. borgmatic consumes this exit code to
decide how to respond. By default, Borg errors (and some warnings) result
in a borgmatic error, while Borg successes don't.

<span class="minilink minilink-addedin">New in borgmatic version 2.1.0</span>
borgmatic elevates several Borg warnings to errors by default. For instance, if
borgmatic doesn't have permission to read a configured source directory during
backup, Borg indicates that with a warning exit code (`105`). And starting in
borgmatic 2.1.0, that exit code is considered an error, so you'll actually find
out about files that borgmatic can't read.

<span class="minilink minilink-addedin">With Borg version 1.4+</span> If the
default behavior isn't sufficient for your needs, you can customize how
borgmatic interprets [Borg's exit
codes](https://borgbackup.readthedocs.io/en/stable/internals/frontends.html#message-ids).

For instance, this borgmatic configuration elevates a Borg warning about source files
changing during backup (exit code `100`)—and only those warnings—to
errors:

```yaml
borg_exit_codes:
    - code: 100
      treat_as: error
```

The following configuration does that *and* squashes errors about Borg
encountering file permissions issues during backup (exit code `105`) to
warnings.

```yaml
borg_exit_codes:
    - code: 100
      treat_as: error
    - code: 105
      treat_as: warning
```

If you don't know the exit code for a particular Borg error or warning you're
experiencing, you can usually find it in your borgmatic output when `--verbosity
2` is enabled. For instance, here's a snippet of that output when a backup file
is not found:

```
/noexist: stat: [Errno 2] No such file or directory: '/noexist'
...
terminating with warning status, rc 107
```

So if you want to configure borgmatic's interpretation of this warning, the exit
status to use is `107`. Note however that in the particular case of missing
files, there's a separate [`source_directories_must_exist`
option](https://torsion.org/borgmatic/reference/configuration/#source_directories_must_exist-option)
that can catch such problems before Borg even runs.

<span class="minilink minilink-addedin">With Borg version 1.2 and earlier</span>
Older versions of Borg didn't support granular exit codes, but still
distinguished between Borg errors and warnings. For instance, to elevate Borg
warnings to errors, thereby causing borgmatic to error on them, use the
following borgmatic configuration with Borg 1.2 or below:

```yaml
borg_exit_codes:
    - code: 1
      treat_as: error
```

Be aware though that Borg exits with a warning code for a variety of benign
situations such as files changing while they're being read, so this example
may not meet your needs. Upgrading to Borg 1.4+ is recommended.
