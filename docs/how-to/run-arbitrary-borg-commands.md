---
title: How to run arbitrary Borg commands
eleventyNavigation:
  key: 🔧 Run arbitrary Borg commands
  parent: How-to guides
  order: 12
---
## Running Borg with borgmatic

Borg has several commands and options that borgmatic does not currently
support. Sometimes though, as a borgmatic user, you may find yourself wanting
to take advantage of these off-the-beaten-path Borg features. You could of
course drop down to running Borg directly. But then you'd give up all the
niceties of your borgmatic configuration. You could file a [borgmatic
ticket](https://torsion.org/borgmatic/#issues) or even a [pull
request](https://torsion.org/borgmatic/#contributing) to add the feature. But
what if you need it *now*?

That's where borgmatic's support for running "arbitrary" Borg commands comes
in. Running these Borg commands with borgmatic can take advantage of the
following, all based on your borgmatic configuration files or command-line
arguments:

 * configured repositories, running your Borg command once for each one
 * local and remote Borg executable paths
 * SSH settings and Borg environment variables
 * lock wait settings
 * verbosity


### borg action

<span class="minilink minilink-addedin">New in version 1.5.15</span> The way
you run Borg with borgmatic is via the `borg` action. Here's a simple example:

```bash
borgmatic borg break-lock
```

This runs Borg's `break-lock` command once with each configured borgmatic
repository, passing the repository path in as a Borg-supported environment
variable named `BORG_REPO`. (The native `borgmatic break-lock` action should
be preferred though for most uses.)

You can also specify Borg options for relevant commands. For instance:

```bash
borgmatic borg repo-list --short
```

(No borgmatic `repo-list` action? Try `rlist` or `list` instead or upgrade
borgmatic!)

This runs Borg's `repo-list` command once on each configured borgmatic
repository.

What if you only want to run Borg on a single configured borgmatic repository
when you've got several configured? Not a problem. The `--repository` argument
lets you specify the repository to use, either by its path or its label:

```bash
borgmatic borg --repository repo.borg break-lock
```

And if you need to specify where the repository goes in the command because
there are positional arguments after it:

```bash
borgmatic borg debug dump-manifest :: root
```

The `::` is a Borg placeholder that means: Substitute the repository passed in
by environment variable here.

<span class="minilink minilink-addedin">Prior to version 1.8.0</span>borgmatic
attempted to inject the repository name directly into your Borg arguments in
the right place (which didn't always work). So your command-line in these
older versions didn't support the `::`


### Specifying an archive

For borg commands that expect an archive name, you have a few approaches.
Here's one:

```bash
borgmatic borg --archive latest list '::$ARCHIVE'
```

The single quotes are necessary in order to pass in a literal `$ARCHIVE`
string instead of trying to resolve it from borgmatic's shell where it's not
yet set.

Or if you don't need borgmatic to resolve an archive name like `latest`, you
can do:

```bash
borgmatic borg list ::your-actual-archive-name
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span>borgmatic
provided the archive name implicitly along with the repository, attempting to
inject it into your Borg arguments in the right place (which didn't always
work). So your command-line in these older versions of borgmatic looked more
like:

```bash
borgmatic borg --archive latest list
```

<span class="minilink minilink-addedin">With Borg version 2.x</span> Either of
these will list an archive:

```bash
borgmatic borg --archive latest list '$ARCHIVE'
```

```bash
borgmatic borg list your-actual-archive-name
```

### Limitations

borgmatic's `borg` action is not without limitations:

 * The Borg command you want to run (`create`, `list`, etc.) *must* come first
   after the `borg` action (and any borgmatic-specific arguments). If you have
   other Borg options to specify, provide them after. For instance,
   `borgmatic borg list --progress ...` will work, but
   `borgmatic borg --progress list ...` will not.
 * Do not specify any global borgmatic arguments to the right of the `borg`
   action. (They will be passed to Borg instead of borgmatic.) If you have
   global borgmatic arguments, specify them *before* the `borg` action.
 * Unlike other borgmatic actions, you cannot combine the `borg` action with
   other borgmatic actions. This is to prevent ambiguity in commands like
   `borgmatic borg list`, in which `list` is both a valid Borg command and a
   borgmatic action. In this case, only the Borg command is run.
 * Unlike normal borgmatic actions that support JSON, the `borg` action will
   not disable certain borgmatic logs to avoid interfering with JSON output.
 * The `borg` action bypasses most of borgmatic's machinery, so for instance
   monitoring hooks will not get triggered when running `borgmatic borg create`.
 * <span class="minilink minilink-addedin">Prior to version 1.8.0</span>
   borgmatic implicitly injected the repository/archive arguments on the Borg
   command-line for you (based on your borgmatic configuration or the
   `borgmatic borg --repository`/`--archive` arguments)—which meant you
   couldn't specify the repository/archive directly in the Borg command. Also,
   in these older versions of borgmatic, the `borg` action didn't work for any
   Borg commands like `borg serve` that do not accept a repository/archive
   name.
 * <span class="minilink minilink-addedin">Prior to version 1.7.13</span> Unlike
   other borgmatic actions, the `borg` action captured (and logged) all output,
   so interactive prompts and flags like `--progress` dit not work as expected.
   In new versions, borgmatic runs the `borg` action without capturing output,
   so interactive prompts work.

In general, this `borgmatic borg` feature should be considered an escape
valve—a feature of second resort. In the long run, it's preferable to wrap
Borg commands with borgmatic actions that can support them fully.
