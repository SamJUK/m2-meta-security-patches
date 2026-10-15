# Contributing

Issues and pull requests are welcome: a patch that will not apply, a store it misbehaves on, a hotfix Adobe has published that is not here yet. [Open an issue](https://github.com/SamJUK/m2-meta-security-patches/issues).

## Adding a patch

1. Put Adobe's file in `patches/isolated/` or `patches/emergency/` **unmodified**. Its sha256 must match Adobe's [patch registry](https://repo.magento.com/patch/patch-registry.json).
2. Declare it in `patches/isolated/patches.json` or `patches/emergency/patches.json`. `composer.json` only points at those two files.
   - A new monthly patch is one entry at the end of its base line's `patches` list. The isolated lines are `cumulative`, so the order listed is the order applied, and nothing declares `depends`.
   - A patch that covers several base versions gets a directory named for the patch, with a file per version: `2026-07-001/2.4.8-p5-CE.patch`. Sources resolve against the manifest beside them.
3. Pin the base version with the line's `base` constraint. Do not list the modules a patch touches: a module that has been `replace`d away would take the whole patch with it.
4. Add it to [docs/patches.md](docs/patches.md), and to the coverage table in the README if it changes what a line gets.
5. Add a line under `## Unreleased` in [CHANGELOG.md](CHANGELOG.md). That section becomes the release page.

## Testing

Tests run real Magento installs in Docker, from the [samjuk/magento-ci-testing-env](https://github.com/SamJUK/magento-ci-testing-env) images.

```sh
sh tests/test.sh                                                  # fresh install on every version in tests/matrix.json
bash tests/test.sh samjuk/magento-ci-testing-env 2.4.9 php8.5     # one version
bash tests/upgrade.sh 2.4.9                                       # newest release -> this working tree
FROM=2026.10.09 bash tests/upgrade.sh 2.4.9                       # from a given release
FROM=none TO=2026.10.13 bash tests/upgrade.sh 2.4.9               # fresh install of a published release
```

`tests/upgrade.sh` updates a store the way the README tells one to, then runs Composer again: verify, a further apply that must write nothing, a `magento2-base` reinstall that must heal, a fresh `vendor/`, and `php -l` on every patched file. The runs after the update are where a month that rewrites an earlier month's lines fails.

The full matrix takes a lot of disk and time locally. CI runs it:

- **Pull requests:** add the `run-tests` label.
- **master:** every push that changes something a store installs.
- **Releases:** publishing one installs it from Packagist, fresh and as an update, on every isolated line. Re-run with `gh workflow run post-release.yml -f version=<version>`.

## Pull requests

Branch from `master`, keep each pull request to one change, and use [Conventional Commits](https://www.conventionalcommits.org/) for the title (`feat: add nov 2026 isolated security patches (CE)`).
