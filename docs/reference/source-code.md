---
title: Source code reference
eleventyNavigation:
  key: 🐍 Source code reference
  parent: Reference guides
  order: 3
---
## getting oriented

If case you're interested in [developing on
borgmatic](https://torsion.org/borgmatic/docs/how-to/develop-on-borgmatic/),
here's an abridged primer on how its Python source code is organized to help
you get started. Starting at the top level, we have:

 * [borgmatic](https://projects.torsion.org/borgmatic-collective/borgmatic/src/branch/main/borgmatic): The main borgmatic source module. Most of the code is here. Within that:
   * [actions](https://projects.torsion.org/borgmatic-collective/borgmatic/src/branch/main/borgmatic/actions): borgmatic-specific logic for running each action (create, list, check, etc.).
   * [borg](https://projects.torsion.org/borgmatic-collective/borgmatic/src/branch/main/borgmatic/borg): Lower-level code that's responsible for interacting with Borg to run each action.
   * [commands](https://projects.torsion.org/borgmatic-collective/borgmatic/src/branch/main/borgmatic/commands): Looking to add a new flag or action? Start here. This contains borgmatic's entry point, argument parsing, and shell completion. 
   * [config](https://projects.torsion.org/borgmatic-collective/borgmatic/src/branch/main/borgmatic/config): Code responsible for loading, normalizing, and validating borgmatic's configuration. Interested in adding a new configuration option? Check out `schema.yaml` here.
   * [hooks](https://projects.torsion.org/borgmatic-collective/borgmatic/src/branch/main/borgmatic/hooks): Looking to add a new database, filesystem, or monitoring integration? Start here.
     * [credential](https://projects.torsion.org/borgmatic-collective/borgmatic/src/branch/main/borgmatic/hooks/credential): Credential hooks—for loading passphrases and secrets from external providers.
     * [data_source](https://projects.torsion.org/borgmatic-collective/borgmatic/src/branch/main/borgmatic/hooks/data_source): Database and filesystem hooks—anything that produces data or files to go into a backup archive.
     * [monitoring](https://projects.torsion.org/borgmatic-collective/borgmatic/src/branch/main/borgmatic/hooks/monitoring): Monitoring hooks—integrations with third-party or self-hosted monitoring services.
 * [docs](https://projects.torsion.org/borgmatic-collective/borgmatic/src/branch/main/docs): How-to and reference documentation, including the document you're reading now.
 * [sample](https://projects.torsion.org/borgmatic-collective/borgmatic/src/branch/main/sample): Example configurations for cron and systemd.
 * [scripts](https://projects.torsion.org/borgmatic-collective/borgmatic/src/branch/main/scripts): Dev-facing scripts for things like building documentation and running end-to-end tests.
 * [tests](https://projects.torsion.org/borgmatic-collective/borgmatic/src/branch/main/tests): Automated tests organized by: end-to-end, integration, and unit.

So, broadly speaking, the control flow goes: `commands` → `config` followed by `commands` → `actions` → `borg` and `hooks`.
