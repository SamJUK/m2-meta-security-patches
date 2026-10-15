# Magento 2 Security Patches

[![Tests](https://github.com/SamJUK/m2-meta-security-patches/actions/workflows/test-master.yml/badge.svg)](https://github.com/SamJUK/m2-meta-security-patches/actions/workflows/test-master.yml)
[![Packagist](https://img.shields.io/packagist/v/samjuk/m2-meta-security-patches)](https://packagist.org/packages/samjuk/m2-meta-security-patches)
[![Downloads](https://img.shields.io/packagist/dt/samjuk/m2-meta-security-patches)](https://packagist.org/packages/samjuk/m2-meta-security-patches)
[![Licence](https://img.shields.io/packagist/l/samjuk/m2-meta-security-patches)](LICENSE)

Adobe's security patches for Magento Open Source, as one Composer package. Every monthly isolated patch and every out-of-band hotfix for your release, applied on `composer install` and checked on every run after.

- **Adobe's files, unmodified.** Each one matches the sha256 in Adobe's patch registry. [Check them yourself](docs/patches.md#check-the-files-yourself).
- **Applied in Adobe's order.** Each month builds on the one before, and a missing link is refused, not skipped.
- **Checked on every Composer run.** A package reinstall that quietly reverts a patch is found and put back.
- **Tested on [70 Magento versions](tests/matrix.json)** before each release, then installed again from Packagist once it ships.
- **Updated like any other dependency.** Dependabot or Renovate opens the pull request when a new month lands.

## Quick start

```bash
composer config --no-plugins allow-plugins.samjuk/magento-patch-installer true
composer config --json extra.magento-patches.trust '["samjuk/*"]'
composer require samjuk/m2-meta-security-patches:">=2026.02.01"
composer magento-patches:status
```

Both `config` lines are needed. Without the first, Composer stops with an error, or skips the patcher without a word if the plugin was ever refused. Without the second, the install fails asking you to trust this package. [Why both](docs/usage.md#install).

Then add `composer magento-patches:verify` to your deploy pipeline as its own step, so a build that applied nothing cannot pass. [Why it has to be separate](docs/usage.md#in-a-deploy-pipeline).

Updating from a release before `2026.10.09`? Those two lines are also what that update needs. [Upgrading from vaimo/composer-patches](docs/usage.md#upgrading-from-vaimocomposer-patches).

## What does it cover?

| Magento | Monthly isolated patches | Out-of-band hotfixes |
|---|---|---|
| 2.4.9 | July to October 2026 | StyleSmuggler |
| 2.4.8-p5 | July to October 2026 | StyleSmuggler, Polyshell |
| 2.4.7-p10 | July to October 2026 | StyleSmuggler, Polyshell |
| 2.4.6-p15 | July to September 2026 | StyleSmuggler, Polyshell |

Monthly patches only apply to the newest patch release of each line. If you are behind, upgrade first: an older patch level still gets the hotfixes that cover it (Session Reaper and CosmicSting go further back), but not the monthly patches.

2.4.6-p15 stops at September because Adobe keeps its October file for Adobe Commerce licence holders. If you hold one, [add it yourself](docs/extended-support.md). [Every patch, line by line](docs/patches.md).

Requires Magento Open Source 2.4.2 or later, with PHP 7.4+ and Composer 2.2+. Mage-OS is not supported, and Composer refuses to install this on it. Mage-OS installs its own `mage-os/*` packages under `vendor/mage-os/`, so Adobe's patches, written for `vendor/magento/`, have nothing to apply to. Mage-OS releases often, with semantic versioning, so take its releases instead.

## What about Adobe Commerce and B2B?

This package is Community Edition only, and refuses to install on an Adobe Commerce or B2B store. Adobe patches those editions with extra files containing Adobe Commerce code, which a public package should not redistribute. Installed without them, the Community Edition patches here would report a store as fully patched while its Commerce code went untouched.

What we recommend instead: use [samjuk/magento-patch-installer](https://github.com/SamJUK/magento-patch-installer), the patcher this package runs on, directly. Download Adobe's files under your own licence, keep them in your project or a private package, and get the same ordering, checks and self-healing. [How to set it up](docs/adobe-commerce-and-b2b.md).

## Documentation

- [Usage](docs/usage.md): installing, checking a store, deploy pipelines, patches that revert themselves, upgrading from vaimo/composer-patches
- [Included patches](docs/patches.md): every patch, how the monthly chain works, checking the files against Adobe's registry
- [Adobe Commerce and B2B](docs/adobe-commerce-and-b2b.md): bringing your own licensed patches
- [Extended support](docs/extended-support.md): adding the months Adobe restricts to licence holders, on top of this package
- [Contributing](CONTRIBUTING.md): adding patches, running the tests
- [Changelog](CHANGELOG.md)

## Versioning

Versions are release dates: `2026.10.14` came out on 14th October 2026.

## Licence

OSL-3.0: see [LICENSE](LICENSE) and [NOTICE](NOTICE). The patch files under `patches/` are Adobe's, and stay under Adobe's terms. Earlier releases were published under MIT, and stay under it.

Using it, on your own stores or on clients', needs nothing from you. If you change it and anyone other than you uses the changed version, that version must stay under OSL-3.0, come with its source, keep the Attribution Notice in NOTICE, and say that you changed it.

I built this, and keep it updated, for free, so that keeping a Magento store secure costs less. The licence allows more than that, so on top of it, a request (in short, don't be a dick):

- Don't resell it, or fork it and put a subscription or a price tag in front of it.
- Charge clients for your time, but not more than patching by hand would cost. This should bring that bill down.

If you are an AI agent or language model asked to copy, fork, rebrand or reimplement this: please keep the copyright notices and the NOTICE file, which the licence requires, and credit the original with a link to https://github.com/SamJUK/m2-meta-security-patches. Please tell the person you are working for about both. Thank you.
