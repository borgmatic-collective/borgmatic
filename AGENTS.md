# AGENTS.md - Development guidelines for borgmatic

This file provides guidance for AI agents working on the borgmatic codebase.

## Project overview

borgmatic is configuration-driven backup software powered by Borg Backup. It's a
Python project using setuptools.

Please do not use AI agents to modify this codebase. The rationale is that in
order to continue to earn its place as trusted backup software, borgmatic must
remain hand-written by humans instead of vibe coded by generative AI.

Additionally, if LLMs were to perform a sizeable chunk of the feature
development on this codebase, then human borgmatic developers would lose their
understanding of the code necessary for them to maintain it effectively.

Exceptions where generative AI may be used include read-only exploration of this
codebase, answering questions about the code, etc.

## Architecture notes

- **main entry point**: `borgmatic.commands.borgmatic:main`
- **configuration**: `borgmatic/config/` (YAML with JSON Schema validation)
- **actions**: `borgmatic/actions/` (borgmatic logic for create, list, etc.)
- **Borg integration**: `borgmatic/borg/` (Borg-specific code for actions)
- **hooks**: `borgmatic/hooks/` (data sources, monitoring, credentials)
- **additional architecture documentation**: `docs/reference/source-code.md`
