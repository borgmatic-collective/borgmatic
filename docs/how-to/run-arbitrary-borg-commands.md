---
title: How to run arbitrary Borg commands
eleventyNavigation:
  key: 🔧 Run arbitrary Borg commands
  parent: How-to guides
  order: 11
---
## Running Borg with borgmatic

Borg has several commands (and options) that borgmatic does not currently
support. Sometimes though, as a borgmatic user, you may find yourself wanting
to take advantage of these off-the-beaten-path Borg features. You could of
course drop down to running Borg directly. But then you'd give up all the
niceties of your borgmatic configuration. You could file a [borgmatic
ticket](https://torsion.org/borgmatic/#issues) or even a [pull
request](https://torsion.org/borgmatic/#contributing) to add the feature. But
what if you need it *now*?

That's where borgmatic's support for running "arbitrary" Borg commands comes
in. Running Borg commands with borgmatic takes advantage of the following, all
based on your borgmatic configuration files or command-line arguments:

 * configured repositories (automatically runs your Borg command once for each
   one)
 * local and remote Borg binary paths
 * SSH settings and Borg environment variables
 * lock wait settings
 * verbosity


### borg action

<span class="minilink minilink-addedin">New in version 1.5.15</span> The way
you run Borg with borgmatic is via the `borg` action. Here's a simple example:

```bash
borgmatic borg break-lock
```

(No `borg` action in borgmatic? Time to upgrade!)

This runs Borg's `break-lock` command once on each configured borgmatic
repository. Notice how the repository isn't present in the specified Borg
options, as that part is provided by borgmatic.

You can also specify Borg options for relevant commands:

```bash
borgmatic borg rlist --short
```

This runs Borg's `rlist` command once on each configured borgmatic repository.
(The native `borgmatic rlist` action should be preferred for most use.)

What if you only want to run Borg on a single configured borgmatic repository
when you've got several configured? Not a problem.

```bash
borgmatic borg --repository repo.borg break-lock
```

And what about a single archive?

```bash
borgmatic borg --archive your-archive-name rlist
```

### Limitations

borgmatic's `borg` action is not without limitations:

 * The Borg command you want to run (`create`, `list`, etc.) *must* come first
   after the `borg` action. If you have any other Borg options to specify,
   provide them after. For instance, `borgmatic borg list --progress` will work,
   but `borgmatic borg --progress list` will not.
 * borgmatic supplies the repository/archive name to Borg for you (based on
   your borgmatic configuration or the `borgmatic borg --repository`/`--archive`
   arguments), so do not specify the repository/archive otherwise.
 * The `borg` action will not currently work for any Borg commands like `borg
   serve` that do not accept a repository/archive name.
 * Do not specify any global borgmatic arguments to the right of the `borg`
   action. (They will be passed to Borg instead of borgmatic.) If you have
   global borgmatic arguments, specify them *before* the `borg` action.
 * Unlike other borgmatic actions, you cannot combine the `borg` action with
   other borgmatic actions. This is to prevent ambiguity in commands like
   `borgmatic borg list`, in which `list` is both a valid Borg command and a
   borgmatic action. In this case, only the Borg command is run.
 * Unlike normal borgmatic actions that support JSON, the `borg` action will
   not disable certain borgmatic logs to avoid interfering with JSON output.
 * Unlike other borgmatic actions, the `borg` action captures (and logs) all
   output, so interactive prompts or flags like `--progress` will not work as
   expected.

In general, this `borgmatic borg` feature should be considered an escape
valve—a feature of second resort. In the long run, it's preferable to wrap
Borg commands with borgmatic actions that can support them fully.
