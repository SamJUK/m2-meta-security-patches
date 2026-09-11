# Magento 2 / Adobe Commerce Meta Package: Security Patches

[![Test on Master](https://github.com/SamJUK/m2-meta-security-patches/actions/workflows/test-master.yml/badge.svg)](https://github.com/SamJUK/m2-meta-security-patches/actions/workflows/test-master.yml)

This repository contains a Composer meta package for applying security patches to Magento 2 / Adobe Commerce installations. The package aggregates Adobe's isolated security patches and emergency out-of-band patches, protecting your store against known vulnerabilities and CVEs without manual patch hunting.

> **Scope:** Community Edition only, and enforced rather than assumed — this package declares a Composer `conflict` with `magento/product-enterprise-edition` and `magento/product-b2b-edition`, so an Adobe Commerce or B2B store cannot install it. Adobe ships separate patches for those editions; the CE patches here apply cleanly to the packages the editions share and would report a fully patched store while the EE-specific code Adobe patches separately went untouched. Mage-OS is supported.

The primary reason for using a meta package is to simplify the management and application of multiple security patches. Instead of applying each patch individually to each project, you can install this meta package, which will automatically include all the necessary patches.

Future updates can be handled automatically via Dependabot or Renovate, ensuring that your Magento 2 / Adobe Commerce installation stays up-to-date with the latest security fixes without the manual overhead and cost.

> [!IMPORTANT]
> **Upgrading from an earlier release?** This version replaces
> `vaimo/composer-patches` with
> [`samjuk/magento-patch-installer`](https://github.com/SamJUK/magento-patch-installer).
> Add the two lines under [Installation](#installation) *before* you update, or
> `composer update` will stop partway.

## Requirements

- Magento 2.4.2+ (see [matrix.json](tests/matrix.json) for full compatibility)
- PHP 7.4+ (version depends on Magento version)
- Composer 2.2+

## List of Included Security Patches

We break down the included security patches into a few groups:

### Isolated Security Patches

These are the new approach to regular security updates provided by Adobe.

Isolated patches are Adobe's term for a fix shipped on its own rather than rolled into a full patch release. That does not mean they are independent of each other: **each month builds on the one before, so they must be applied in order.** That is why the isolated lines in `patches/isolated/patches.json` are marked `"cumulative": true` — the installer applies them in the order they are listed and refuses to let a link be left out.

Each monthly patch is also built against, and will only apply to, the **latest patch release** of its line at the time it was issued (e.g. `2026-07-001` for the `2.4.8` line only applies to `2.4.8-p5`, not `p4` or earlier). If you're behind on patch levels, catch up first — the patch won't apply otherwise.

- **2026-07-001 (CE)** - Adobe Commerce monthly isolated security release, July 2026. CE-only; EE/B2B variants not currently included in this package.
- **2026-08-001 (CE)** - Adobe Commerce monthly isolated security release, August 2026. CE-only; EE/B2B variants not currently included in this package.
- **2026-09-001 (CE)** - Adobe Commerce monthly isolated security release, September 2026. CE-only; EE/B2B variants not currently included in this package.

For detailed information on each patch, see the patches in [patches/isolated/](patches/isolated/).

### Emergency Security Patches

These patches address critical vulnerabilities out of band security issues that require immediate attention:

- **CVE-2024-34102** - CosmicSting vulnerability affecting Magento 2.4.7 and earlier
- **CVE-2025-54236** - Session security vulnerability
- **APSB25-94** - Polyshell vulnerability affecting Magento 2.4.9-alpha2 and earlier
- **APSB26-146 (VULN-39341, StyleSmuggler)** - CVE-2026-75650, unauthenticated RCE via GraphQL style property injection into admin email preview/reminder rendering, actively exploited. Critical (CVSS 10.0). Affects 2.4.6-2.4.9; one patch per base version, base 2.4.4/2.4.5 not covered by this package.

For detailed information on each patch, see the patches in [patches/emergency/](patches/emergency/).

## Changes we make to Adobe's patches

**New monthly drops go in unmodified.** Adobe's patch file is added as-is; nothing is rewritten on the way in.

Two historical edits remain in the patch files added before `samjuk/magento-patch-installer` existed, both of which were workarounds for `vaimo/composer-patches` and neither of which is needed any more:

- **Hunks against project root files were repointed at `vendor/magento/magento2-base/`.** vaimo patched before Magento deployed those files to the root, so a clean install had nothing to patch yet. The installer now resolves the two copies of a root-mapped file from the package's own `extra.map` and keeps both patched, whichever path the hunk names — so the repointed files and Adobe's originals both work.
- **`vendor/bin/patch-status` hunks were stripped.** Adobe regenerates this reporting CLI every month, so re-applying used to abort the whole run with `already exists in working directory`. The installer now recognises a file it wrote for an earlier patch in the same chain and replaces it, so the hunk can stay.

Leaving the existing files as they are is deliberate: they work, and rewriting them would churn the patches that protect the stores already running them.

## Patches that revert themselves

Reinstalling or updating `magento/magento2-base` re-extracts the package and reverts the patched files, including the ~120 it deploys to the project root. Under `vaimo/composer-patches` nothing noticed: `composer patch:list` still reported `[APPLIED]` and `composer install` still said `Nothing to patch` ([vaimo/composer-patches#162](https://github.com/vaimo/composer-patches/issues/162)).

`samjuk/magento-patch-installer` re-checks every target against the working tree on every run, so this heals itself — the next `composer install` re-applies whatever the reinstall reverted, and `composer patches:verify` exits non-zero in the window before it does. No manual `patch:redo` step, and nothing to wire into a script.

## Installation

To install the meta package, use Composer by running the following command in your Magento 2 root directory:

```bash
composer require samjuk/m2-meta-security-patches:">=2026.02.01"
```

Patches are applied by [samjuk/magento-patch-installer](https://github.com/SamJUK/magento-patch-installer), which comes in as a dependency. It runs after Magento's own root-file deploy, checks on every Composer run that each patch is still applied, and fails the run when one is not.

### Allow the installer to run (required)

Composer does not run a plugin it has not been told to trust. In an
interactive terminal it asks; in CI it does not — it skips the plugin, prints
nothing about it, and exits `0` having applied no patches at all.

```bash
composer config --no-plugins allow-plugins.samjuk/magento-patch-installer true
```

### Trust this package (required)

Patching from dependencies is opt-in. Nothing outside your own `composer.json` is read until you say so, so this one line is what switches the meta package on:

```bash
composer config --json "extra.magento-patches.trust" '["samjuk/*"]'
```

Which writes:

```json
{
  "extra": {
    "magento-patches": {
      "trust": ["samjuk/*"]
    }
  }
}
```

### Checking a store

```bash
composer patches:list      # every patch this package ships, and which are for you
composer patches:status    # this store: version, support, and every patch's state
composer patches:status -v # per-target detail, including anything not covered
composer patches:verify    # exit 0 all applied, 1 missing, 2 conflict, 3 misconfigured
composer patches:apply     # apply whatever is missing
```

`patches:list` reads nothing from the working tree, so it answers before
`composer install` has ever run — useful for deciding whether this package
covers your release line at all.

`composer patches:verify` is the one to put in a deploy pipeline, as its own step rather than relying on the install: `composer install --no-plugins`, and a missing `allow-plugins` entry, each run a whole install and exit `0` having applied nothing, and neither can be reported from inside a plugin that never ran.

A patch that cannot apply fails the Composer run by default; `extra.magento-patches.allow-unpatched` overrides that if you need it.

## Versioning

The versioning of this meta package follows date based versioning to indicate the release date of the included patches. For example, a version `2024.10.15` indicates that the package was released on October 15, 2024.

## Development

To contribute to the development of this meta package:

1. Clone the repository
2. Drop Adobe's patch file into `patches/isolated/` or `patches/emergency/` **unmodified**
3. Declare it in `patches/isolated/patches.json` or `patches/emergency/patches.json` — `composer.json` only lists those files. A new monthly patch is one entry appended to the end of that base line's `patches` list. The isolated lines are marked `"cumulative": true`, which means the order they are listed in *is* the order they apply in, so nothing declares `depends` and no link can be left out
   - A patch that spans base versions gets its own directory named for the patch, with a file per version inside; sources resolve against the manifest beside them, so an entry names `2026-07-001/2.4.8-p5-CE.patch` and nothing more
4. Pin the base version with the line's `base` constraint. Do **not** list the modules a patch touches: a module that has been `replace`d away would take the whole patch down with it
5. Run tests locally with `sh tests/test.sh` (requires Docker)
6. Submit a pull request

## Testing

### Automated Testing

Full E2E tests are run via GitHub Actions:

- **On master/main commits**: Tests run automatically on every push
- **On pull requests**: Add the `run-tests` label to trigger the test suite

The test suite validates the package installation across multiple Magento versions and PHP versions (see [matrix.json](tests/matrix.json) for the complete matrix).

### Local Testing

You can run the full test suite locally with Docker:

```sh
sh tests/test.sh
```

This will test the package installation across all supported Magento/PHP version combinations. Be aware, this can take a significant amount of disk space and time.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure tests pass locally
5. Submit a pull request
