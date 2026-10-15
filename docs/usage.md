# Usage

Patches are applied by [samjuk/magento-patch-installer](https://github.com/SamJUK/magento-patch-installer), which this package requires. It runs after Magento has deployed its root files, checks every patch against the files on disk on every Composer run, and fails the run when one is missing. Its README has the full reference; this page covers what a store running this package needs.

## Install

```bash
composer config --no-plugins allow-plugins.samjuk/magento-patch-installer true
composer config --json extra.magento-patches.trust '["samjuk/*"]'
composer require samjuk/m2-meta-security-patches:">=2026.02.01"
```

**Why allow the plugin?** Composer only runs plugins it has been told to trust. In a terminal it asks. In CI it stops with an error naming the plugin. If anyone ever answered "n" to that question, or set the entry to `false`, Composer skips the plugin without a word and exits `0` having applied no patches.

**Why trust the package?** Patching from dependencies is opt-in. Nothing outside your own `composer.json` is read until you name it, so this is the line that switches the package on. It writes:

```json
{
  "extra": {
    "magento-patches": {
      "trust": ["samjuk/*"]
    }
  }
}
```

**Why `>=2026.02.01`?** Versions are release dates, so an open lower bound picks up every new month. Composer still filters out betas on stability.

## Check a store

```bash
composer magento-patches:list      # every patch this package ships, and which are for this store
composer magento-patches:status    # this store: version, support dates, and every patch's state
composer magento-patches:status -v # per-file detail, including anything not covered
composer magento-patches:verify    # exit 0 all applied, 1 missing, 2 conflict, 3 misconfigured
composer magento-patches:apply     # apply whatever is missing
```

`list` changes nothing and runs no git. Use it to see whether this package covers your release line at all.

## In a deploy pipeline

Run `composer magento-patches:verify` as its own step after the install, and let a non-zero exit fail the build:

```yaml
- run: composer install --no-interaction
- run: composer magento-patches:verify --no-interaction
```

The install applies patches, but two ordinary things stop it running at all: `composer install --no-plugins`, and an `allow-plugins` entry set to `false`. Both install everything and exit `0` with nothing patched, and a plugin that never ran cannot report it. Only a separate step catches that.

A patch that cannot apply fails the Composer run. `extra.magento-patches.allow-unpatched` turns that off if you need to, and is not something to leave set.

## Patches that revert themselves

Reinstalling or updating `magento/magento2-base` re-extracts the package and puts back the unpatched files, including about 120 it deploys to the project root. The installer checks every file on every run, so the next `composer install` re-applies whatever was reverted, and `magento-patches:verify` exits non-zero in the window before it does.

There is no re-apply step to remember. `vaimo/composer-patches`, which earlier releases used, never noticed: it kept reporting `[APPLIED]` over the reverted files ([vaimo/composer-patches#162](https://github.com/vaimo/composer-patches/issues/162)).

## Switching a patch off

If a patch breaks something you cannot fix straight away, skip it in your own `composer.json`, with the reason:

```json
"extra": {
    "magento-patches": {
        "sources": {
            "samjuk/m2-meta-security-patches": {
                "skip": { "2026-10-001@2.4.9": "breaks our checkout, ticket #123" }
            }
        }
    }
}
```

A skip takes the patch off disk, not just out of future installs, and every later month built on it goes with it. It stays visible in every report until you remove it. See [choosing which patches apply](https://github.com/SamJUK/magento-patch-installer#choosing-which-patches-apply).

The same applies if another patch package you trust ships a fix that clashes with one here: skip one side, but only if the other really carries the same fix.

## Upgrading from vaimo/composer-patches

Releases before `2026.10.09` applied patches with `vaimo/composer-patches`. If that is what you are on, run the two `config` lines from [Install](#install) **before** you update. Without them the update stops partway, with no patcher installed and Magento's root files (`pub/index.php`, `app/bootstrap.php` and the rest) not deployed. To recover, add the two lines, then run `composer reinstall magento/magento2-base`: that puts the root files back, and the patcher applies everything on the same run.

You do not need to remove vaimo yourself. The update removes it, and it reverts its own patches on the way out before the new installer applies them again.
