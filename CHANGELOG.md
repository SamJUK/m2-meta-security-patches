# Changelog

Notable changes, newest first.

## Unreleased

First stable release on
[`samjuk/magento-patch-installer`](https://github.com/SamJUK/magento-patch-installer),
replacing `vaimo/composer-patches`. Same isolated and emergency patches as
`2026.09.08`, now shipped exactly as Adobe publishes them. The two betas below
have the detail.

### ⚠️ Action required before updating

**Add these two lines before you update, or `composer update` will fail:**

```sh
composer config --no-plugins allow-plugins.samjuk/magento-patch-installer true
composer config --json extra.magento-patches.trust '["samjuk/*"]'
```

Composer refuses to run a plugin it has not been told to trust, and refuses to
read patches from a package you have not named. Without both lines the update
stops partway, leaving no patcher installed until they are added. Adding them
and running `composer install` recovers fully.

You do not need to remove `vaimo/composer-patches` by hand. The update removes
it, and it reverts its own patches on the way out before the new installer
re-applies them.

Then add `composer magento-patches:verify` to your deploy pipeline as its own
step. `composer install --no-plugins`, or a missing `allow-plugins` entry,
installs everything, applies nothing and exits `0`. Only a separate step can
catch that.

### Changed

- Patches are applied by `samjuk/magento-patch-installer` `^0.2.1`. Every patch
  is re-checked against the files on disk on each Composer run, so a patch
  reverted by a package reinstall is found and re-applied, not reported as
  applied.
- The commands are `composer magento-patches:list`, `:status`, `:verify` and
  `:apply`. vaimo's `patch:*` commands go with vaimo.
- A patch whose file belongs to a replaced package no longer skips the whole
  patch. ([#7](https://github.com/SamJUK/m2-meta-security-patches/issues/7))
- Only packages named in `extra.magento-patches.trust` may patch your store.
  ([vaimo#157](https://github.com/vaimo/composer-patches/issues/157))
- Adobe Commerce and B2B stores can no longer install this package. Adobe
  patches those editions separately, and these Community Edition patches would
  report a fully patched store while that code went untouched.
- The July, August and StyleSmuggler (VULN-39341) patches are Adobe's files byte
  for byte, sha256-matched against Adobe's patch registry. That drops the two
  vaimo workarounds and brings back `vendor/bin/patch-status`, Adobe's reporting
  tool. A store that is already patched only gains that file.
- July's 2.4.8-p5 patch is Adobe's current build of it. Adobe re-issued the file
  after release day with different context lines and the same changes.

### Testing

- Upgrade from `2026.09.08` (vaimo) on 2.4.9, 2.4.8-p5, 2.4.7-p10 and
  2.4.6-p15, and from `2026.09.11-beta2` on 2.4.9, against the published
  installer: every target applied, a second install writes nothing, a
  `magento2-base` reinstall heals, and a fresh `vendor/` comes back patched.
- Fresh install on the same four lines, and the upgrade on 12 older patch levels
  plus Mage-OS 2.2.1 and 1.3.1.

## 2026.09.11-beta2 — 2026-09-12

Second beta. Same patches as `beta1`; the installer underneath moved to
`0.2.0`.

### Changed

- **Breaking for scripts.** The commands are now `magento-patches:*`, not
  `patches:*`. Composer treats `patch` as an abbreviation of `patches`, so on
  a store also running vaimo you could not tell which tool a command would
  reach.

  Update any pipeline that calls `patches:verify`. It fails loudly, not
  silently. Patching on install and update is unaffected.

## 2026.09.11-beta1 — 2026-09-11

**Pre-release.** Tagged beta on purpose: stores on a stable constraint such as
`>=2026.02.01` will not pick this up, because Composer filters it out on
stability rather than on version. Opt in explicitly to try it:

```sh
composer require samjuk/m2-meta-security-patches:2026.09.11-beta1@beta
```

Please report anything you hit — a bug, confusing output, a store it will not
install on, or a view on how it should behave.
<https://github.com/SamJUK/m2-meta-security-patches/issues>

### ⚠️ Action required before updating

This release replaces `vaimo/composer-patches` with
[`samjuk/magento-patch-installer`](https://github.com/SamJUK/magento-patch-installer).
**Add these two lines before you update, or `composer update` will fail:**

```sh
composer config --no-plugins allow-plugins.samjuk/magento-patch-installer true
composer config --json extra.magento-patches.trust '["samjuk/*"]'
```

Composer refuses to run a plugin it has not been told to trust, and refuses to
read patches from a package you have not named. Without both lines the update
stops partway, leaving no patcher installed until they are added. Adding them
and running `composer install` recovers fully.

You do not need to remove `vaimo/composer-patches` by hand. It is a dependency
of this package, so the update removes it, and it reverts its own patches on
the way out before the new installer re-applies them.

### Changed

- Patches are applied by `samjuk/magento-patch-installer` rather than
  `vaimo/composer-patches`. Every patch is re-checked against the files on disk
  on each Composer run, so a patch reverted by a package reinstall is found and
  re-applied instead of being reported as still applied.
- A patch whose file belongs to a replaced package no longer skips the whole
  patch. Patches are split per file, so an uncoverable target is named in the
  report and skipped while the rest still applies. ([#7](https://github.com/SamJUK/m2-meta-security-patches/issues/7))
- Only packages you name in `extra.magento-patches.trust` may patch your store.
  Previously any installed dependency could declare patches.
  ([vaimo#157](https://github.com/vaimo/composer-patches/issues/157))
- Adobe Commerce and B2B stores can no longer install this package. Adobe ships
  separate patches for those editions; the Community Edition patches here apply
  to the packages the editions share and would report a fully patched store
  while the code Adobe patches separately went untouched.
- Declarations moved out of `composer.json` into
  `patches/emergency/patches.json` and `patches/isolated/patches.json`.
- Each base line lists its patches in one `patches` list. The isolated lines are
  marked `cumulative`, so the order they are listed in is the order they apply.

### Testing

- 82 Magento and Mage-OS images
- Live upgrade from `vaimo/composer-patches` on a 2.4.7-p10 store — 59 of 59
  targets applied
- Clean install on a 2.4.9 store with the Hyvä theme — 57 of 57
- Mage-OS 1.0.0 and 1.0.1 dropped from the matrix: both ship a
  `composer-root-update-plugin` incompatible with the Composer in their own
  image, so `composer list` fatals before anything of ours runs. No patch here
  targets either version.
  ([magento-ci-testing-env#54](https://github.com/SamJUK/magento-ci-testing-env/issues/54))
