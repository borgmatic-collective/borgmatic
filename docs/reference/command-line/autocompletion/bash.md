---
title: bash
eleventyNavigation:
  key: bash
  parent: ➡️  Autocompletion
---
borgmatic includes an autocompletion script for
[Bash](https://www.gnu.org/software/bash/) to support tab-completing
command-line actions and flags. Depending on how you installed borgmatic, this
may be enabled by default.

If completions aren't enabled, start by installing the `bash-completion` Linux
package or the
[`bash-completion@2`](https://formulae.brew.sh/formula/bash-completion@2) macOS
Homebrew formula. Then, install the shell completion script globally:

```bash
sudo su -c "borgmatic --bash-completion > $(pkg-config --variable=completionsdir bash-completion)/borgmatic"
```

If you don't have `pkg-config` installed, you can try the following path
instead:

```bash
sudo su -c "borgmatic --bash-completion > /usr/share/bash-completion/completions/borgmatic"
```

Or, if you'd like to install the script for only the current user:

```bash
mkdir --parents ~/.local/share/bash-completion/completions
borgmatic --bash-completion > ~/.local/share/bash-completion/completions/borgmatic
```

Finally, restart your shell (`exit` and open a new shell) so the completions
take effect.
