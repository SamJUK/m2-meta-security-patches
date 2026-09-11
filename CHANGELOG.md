# Changelog

Notable changes, newest first.

## Unreleased

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

### Changed

- Patches are applied by `samjuk/magento-patch-installer` rather than
  `vaimo/composer-patches`. Every patch is re-checked against the files on disk
  on each Composer run, so a patch reverted by a package reinstall is found and
  re-applied instead of being reported as still applied.
- Adobe Commerce and B2B stores can no longer install this package. Adobe ships
  separate patches for those editions; the Community Edition patches here apply
  to the packages the editions share and would report a fully patched store
  while the code Adobe patches separately went untouched.
- Declarations moved out of `composer.json` into
  `patches/emergency/patches.json` and `patches/isolated/patches.json`.
- Each base line lists its patches in one `patches` list. The isolated lines are
  marked `cumulative`, so the order they are listed in is the order they apply.
