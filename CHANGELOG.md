# Changelog

Notable changes, newest first.

## Unreleased

Nothing yet.

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
