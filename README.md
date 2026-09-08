# Magento 2 / Adobe Commerce Meta Package: Security Patches

[![Test on Master](https://github.com/SamJUK/m2-meta-security-patches/actions/workflows/test-master.yml/badge.svg)](https://github.com/SamJUK/m2-meta-security-patches/actions/workflows/test-master.yml)

This repository contains a Composer meta package for applying security patches to Magento 2 / Adobe Commerce installations. The package aggregates Adobe's isolated security patches and emergency out-of-band patches, protecting your store against known vulnerabilities and CVEs without manual patch hunting.

> **Scope:** Community Edition (CE) only. EE/B2B is not currently supported — see [Isolated Security Patches](#isolated-security-patches) below.

The primary reason for using a meta package is to simplify the management and application of multiple security patches. Instead of applying each patch individually to each project, you can install this meta package, which will automatically include all the necessary patches.

Future updates can be handled automatically via Dependabot or Renovate, ensuring that your Magento 2 / Adobe Commerce installation stays up-to-date with the latest security fixes without the manual overhead and cost.

## Requirements

- Magento 2.4.2+ (see [test-matrix.json](test-matrix.json) for full compatibility)
- PHP 7.4+ (version depends on Magento version)
- Composer 2.x

## List of Included Security Patches

We break down the included security patches into a few groups:

### Isolated Security Patches

These are the new approach to regular security updates provided by Adobe.

Isolated patches are **non-cumulative and must be applied in sequence**. Each monthly patch is built against, and will only apply to, the **latest patch release** of its line at the time it was issued (e.g. `2026-07-001` for the `2.4.8` line only applies to `2.4.8-p5`, not `p4` or earlier). If you're behind on patch levels, catch up first — the patch won't apply otherwise.

- **2026-07-001 (CE)** - Adobe Commerce monthly isolated security release, July 2026. CE-only; EE/B2B variants not currently included in this package.
- **2026-08-001 (CE)** - Adobe Commerce monthly isolated security release, August 2026. CE-only; EE/B2B variants not currently included in this package.
- **2026-09-001 (CE)** - Adobe Commerce monthly isolated security release, September 2026. CE-only; EE/B2B variants not currently included in this package.

For detailed information on each patch, see the patches in [src/patches/isolated/](src/patches/isolated/).

### Emergency Security Patches

These patches address critical vulnerabilities out of band security issues that require immediate attention:

- **CVE-2024-34102** - CosmicSting vulnerability affecting Magento 2.4.7 and earlier
- **CVE-2025-54236** - Session security vulnerability
- **APSB25-94** - Polyshell vulnerability affecting Magento 2.4.9-alpha2 and earlier
- **APSB26-146 (VULN-39341, StyleSmuggler)** - CVE-2026-75650, unauthenticated RCE via GraphQL style property injection into admin email preview/reminder rendering, actively exploited. Critical (CVSS 10.0). Affects 2.4.6-2.4.9; one patch per base version, base 2.4.4/2.4.5 not covered by this package.

For detailed information on each patch, see the patches in [src/patches/emergency/](src/patches/emergency/).

## Changes we make to Adobe's patches

The patch files in this repo are not byte-identical to the ones Adobe ships. Two kinds of change are applied:

### Hunks targeting project root files are repointed at their owning package

Adobe's patches are written against a project root, so some hunks target files that sit at the root but are owned by a package that copies them into place on install. `magento/magento2-base` is the usual culprit (for example `nginx.conf.sample` and `lib/web/underscore.js`).

These can't be patched at their root path. `vaimo/composer-patches` applies patches on `PRE_AUTOLOAD_DUMP`, but `magento/magento-composer-installer` deploys the root files on `POST_INSTALL_CMD`, which runs later. On a clean install (fresh checkout, no `vendor/`) those files don't exist yet when patching runs, so the patch fails and halts the run before the deploy that would have created them. Every subsequent `composer install` hits the same state.

We repoint such hunks at the owning package path instead (`vendor/magento/magento2-base/...`). The file always exists at patch time, and the deploy afterwards copies the patched version to the project root. This works for both clean installs and adding the package to an existing install.

### `vendor/bin/patch-status` is removed

Adobe's patches add `vendor/bin/patch-status`, a version-reporting CLI rather than a security fix. It is added as a new file, so it only applies once: if the file is already there, re-applying fails with `vendor/bin/patch-status: already exists in working directory`, and that takes down `composer patch:redo` for every patch in the run, not just the one containing the hunk.

Since it isn't a security fix and it blocks patches being re-applied, we strip it.

## Known issue: patches silently revert

Reinstalling or updating `magento/magento2-base` re-extracts the package and reverts the patched files. `composer patch:list` will still report the patches as `[APPLIED]` and `composer install` will report `Nothing to patch`, so nothing warns you.

This is a bug in `vaimo/composer-patches`, not something specific to this package: it records applied state against the patch file and never re-checks the target. It affects ordinary single-package patches too. See [vaimo/composer-patches#162](https://github.com/vaimo/composer-patches/issues/162).

To re-apply them:

```bash
composer patch:redo
```

Then confirm:

```bash
grep -m1 'Underscore.js 1.13' lib/web/underscore.js   # expect 1.13.8
grep -c customer_address nginx.conf.sample            # expect 1
```

Don't wire this into a `post-install-cmd` script. `composer patch:redo` triggers the `post-install-cmd` causing an infinite loop. Run it manually after any operation that reinstalls `magento/magento2-base`.

## Installation

To install the meta package, use Composer by running the following command in your Magento 2 root directory:

```bash
composer require samjuk/m2-meta-security-patches:">=2026.02.01"
```

The patches will be automatically applied during installation via [vaimo/composer-patches](https://github.com/vaimo/composer-patches).

### Restrict patch sources (recommended)

By default, `vaimo/composer-patches` allows **any** dependency to declare patches, which is a supply chain risk — a compromised or malicious package could silently patch your codebase. See [vaimo/composer-patches#157](https://github.com/vaimo/composer-patches/issues/157). Restrict patching to only this meta package:

```bash
composer config --json "extra.patcher" '{"sources":{"packages":["samjuk/m2-meta-security-patches"]}}'
```

This writes the following to your root `composer.json` (merge manually if `extra.patcher` already has other config, since the command above overwrites the whole key):

```json
{
  "extra": {
    "patcher": {
      "sources": {
        "packages": ["samjuk/m2-meta-security-patches"]
      }
    }
  }
}
```

## Versioning

The versioning of this meta package follows date based versioning to indicate the release date of the included patches. For example, a version `2024.10.15` indicates that the package was released on October 15, 2024.

## Development

To contribute to the development of this meta package:

1. Clone the repository
2. Make your changes in the `src/` directory
3. Add or update patches in `src/patches/`
4. Update `src/composer.json` with patch configuration
5. Run tests locally with `sh tests/test.sh` (requires Docker)
6. Submit a pull request

## Testing

### Automated Testing

Full E2E tests are run via GitHub Actions:

- **On master/main commits**: Tests run automatically on every push
- **On pull requests**: Add the `run-tests` label to trigger the test suite

The test suite validates the package installation across multiple Magento versions and PHP versions (see [test-matrix.json](tests/test-matrix.json) for the complete matrix).

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
