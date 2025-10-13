---
title: Runtime directory
eleventyNavigation:
  key: 📁 Runtime directory
  parent: ⚙️  Configuration
---
<span class="minilink minilink-addedin">New in version 1.9.0</span> borgmatic
uses a runtime directory for temporary file storage, such as for streaming
database dumps to Borg, creating filesystem snapshots, saving bootstrap
metadata, and so on. To determine the path for this runtime directory, borgmatic
probes the following values:

 1. The `user_runtime_directory` borgmatic configuration option.
 2. The `XDG_RUNTIME_DIR` environment variable, usually `/run/user/$UID`
    (where `$UID` is the current user's ID), automatically set by PAM on Linux
    for a user with a session.
 3. <span class="minilink minilink-addedin">New in version 1.9.2</span>The
    `RUNTIME_DIRECTORY` environment variable, set by systemd if
    `RuntimeDirectory=borgmatic` is added to borgmatic's systemd service file.
 4. <span class="minilink minilink-addedin">New in version 1.9.1</span>The
    `TMPDIR` environment variable, set on macOS for a user with a session,
    among other operating systems.
 5. <span class="minilink minilink-addedin">New in version 1.9.1</span>The
    `TEMP` environment variable, set on various systems.
 6. <span class="minilink minilink-addedin">New in version 1.9.2</span>
    Hard-coded `/tmp`. <span class="minilink minilink-addedin">Prior to
    version 1.9.2</span>This was instead hard-coded to `/run/user/$UID`.

You can see the runtime directory path that borgmatic selects by running with
`--verbosity 2` and looking for `Using runtime directory` in the output.

Regardless of the runtime directory selected, borgmatic stores its files
within a `borgmatic` subdirectory of the runtime directory. Additionally, in
the case of `TMPDIR`, `TEMP`, and the hard-coded `/tmp`, borgmatic creates a
randomly named subdirectory in an effort to reduce path collisions in shared
system temporary directories.

<span class="minilink minilink-addedin">Prior to version 1.9.0</span>
borgmatic created temporary streaming database dumps within the `~/.borgmatic`
directory by default. At that time, the path was configurable by the
`borgmatic_source_directory` configuration option (now deprecated).
