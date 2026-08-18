---
title: fish
eleventyNavigation:
  key: fish
  parent: ➡️  Autocompletion
---
borgmatic includes an autocompletion script for [fish
shell](https://fishshell.com/) to support tab-completing command-line actions
and flags. Depending on how you installed borgmatic, this may be enabled by
default.

If completions aren't enabled, install the completions file globally:

```shell
borgmatic --fish-completion | sudo tee /usr/share/fish/vendor_completions.d/borgmatic.fish
source /usr/share/fish/vendor_completions.d/borgmatic.fish
```
