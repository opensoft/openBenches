# cloudBench source transition

The active portable bench is [opensoft/cloudBench](https://github.com/opensoft/cloudBench).
The local directory remains `sysBenches/cloudBench`. The temporary repository
name `cloudBench-public` is no longer the canonical name.

## Existing checkouts

Preserve local changes before updating an OpenBenches checkout. After moving the
parent checkout to a revision that uses the current source URL, synchronize the
submodule URL and install the exact revision pinned by that parent:

```bash
git submodule sync -- sysBenches/cloudBench
git submodule update --init -- sysBenches/cloudBench
```

Do not change the pin to the latest branch tip: `.gitmodules`, the bench catalog,
the gitlink, and `config/release-lock.json` describe one reviewed source identity.
These source operations do not rebuild images or restart a running bench.

## Historical releases

The public repository starts from an independently initialized clean source
snapshot. Older release tags may pin revisions from the original private
history that are not present in the public repository. Existing release tags
have not been rewritten.

Use a current source revision for a clean public installation. Restoring a
historical private revision requires an authorized, explicit private-source
recovery procedure; do not import that history into the public bench to make an
old lockfile resolve.
