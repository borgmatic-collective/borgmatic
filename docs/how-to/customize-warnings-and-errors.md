---
title: How to customize warnings and errors
eleventyNavigation:
  key: 💥 Customize warnings/errors
  parent: How-to guides
  order: 13
---
## When things go wrong

After Borg runs, it indicates whether it succeeded via its exit code, a
numeric ID indicating success, warning, or error. borgmatic consumes this exit
code to decide how to respond. Normally, a Borg error results in a borgmatic
error, while a Borg warning or success doesn't.

<span class="minilink minilink-addedin">With Borg version 1.4+</span> If the
default behavior isn't sufficient for your needs, you can customize how
borgmatic interprets [Borg's exit
codes](https://borgbackup.readthedocs.io/en/stable/usage/general.html#return-codes).

For instance, this borgmatic configuration elevates all Borg backup file
permission warnings (exit code `105`)—and only those warnings—to errors:

```yaml
borg_exit_codes:
    - code: 105
      treat_as: error
```

The following configuration does that *and* elevates backup file not found
warnings (exit code `107`) to errors as well:

```yaml
borg_exit_codes:
    - code: 105
      treat_as: error
    - code: 107
      treat_as: error
```

See the full list of [Borg 1.4 error and warning exit
codes](https://borgbackup.readthedocs.io/en/stable/internals/frontends.html#message-ids).
The `rc:` numeric value there tells you the exit code for each.

If you don't know the exit code for a particular Borg error or warning you're
experiencing, you can usually find it in your borgmatic output when `--verbosity
2` is enabled. For instance, here's a snippet of that output when a backup file
is not found:

```
/noexist: stat: [Errno 2] No such file or directory: '/noexist'
...
terminating with warning status, rc 107
```

So if you want to configure borgmatic to treat this as an error instead of a
warning, the exit status to use is `107`.

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
may not meet your needs.

Here's another Borg 1.2 example that squashes Borg errors to warnings:

```yaml
borg_exit_codes:
    - code: 2
      treat_as: warning
```

Be careful with this example though, because it prevents borgmatic from
erroring when Borg errors, which may not be desirable.
