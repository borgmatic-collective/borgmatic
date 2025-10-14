---
title: Container secrets
eleventyNavigation:
  key: Container
  parent: 🔒 Credentials
---
<span class="minilink minilink-addedin">New in version 1.9.11</span> When
running inside a container, borgmatic can read [Docker
secrets](https://docs.docker.com/compose/how-tos/use-secrets/) and [Podman
secrets](https://www.redhat.com/en/blog/new-podman-secrets-command). Creating
those secrets and passing them into your borgmatic container is outside the
scope of this documentation, but here's a simple example of that with [Docker
Compose](https://docs.docker.com/compose/):

```yaml
services:
  borgmatic:
    # Use the actual image name of your borgmatic container here.
    image: borgmatic:latest
    secrets:
      - borgmatic_passphrase
secrets:
  borgmatic_passphrase:
    file: /etc/borgmatic/passphrase.txt
```

This assumes there's a file on the host at `/etc/borgmatic/passphrase.txt`
containing your passphrase. Docker or Podman mounts the contents of that file
into a secret named `borgmatic_passphrase` in the borgmatic container at
`/run/secrets/`.

Once your container secret is in place, you can consume it within your borgmatic
configuration file:

```yaml
encryption_passphrase: "{credential container borgmatic_passphrase}"
```

This reads the secret securely from a file mounted at
`/run/secrets/borgmatic_passphrase` within the borgmatic container.

The `{credential ...}` syntax works for several different options in a borgmatic
configuration file besides just `encryption_passphrase`. For instance, the
username, password, and API token options within database and monitoring hooks
support `{credential ...}`:

```yaml
postgresql_databases:
    - name: invoices
      username: postgres
      password: "{credential container borgmatic_db1}"
```

You can also optionally override the `/run/secrets` directory that borgmatic reads secrets from
inside a container:

```yaml
container:
    secrets_directory: /path/to/secrets
```

But you should only need to do this for development or testing purposes.
