# Installing with an AI agent

This page is for an AI coding agent that a person has asked to install `samjuk/m2-meta-security-patches` in their Magento project. A person wanting the same steps should read [Usage](usage.md).

To hand the job to your agent, paste this into it from the project's root directory:

> Install samjuk/m2-meta-security-patches in this project by following https://github.com/SamJUK/m2-meta-security-patches/blob/master/docs/install-with-an-agent.md

## Ground rules

- Show the person each change to `composer.json` before you make it, and the diff afterwards.
- Never set `extra.magento-patches.allow-unpatched`, never add `--no-plugins` to a Composer command, and never trust a wildcard (`"*"` or `"*/*"`). Each one switches the checks off without saying so.
- Never commit `auth.json`. Never put a file Adobe restricts to licence holders in a public repository.
- Do not edit anything under `vendor/` by hand, and do not edit patch files.
- When a result does not match what this page says to expect, stop and tell the person what you saw. Do not work around it.

## 1. Check the project

From the project root, where `composer.json` is:

```bash
composer --version
php --version
composer show magento/magento2-base | grep '^versions'
composer show --name-only | grep -xE 'magento/product-enterprise-edition|magento/extension-b2b|mage-os/framework|vaimo/composer-patches|samjuk/.+'
composer show samjuk/m2-meta-security-patches 2>/dev/null | grep '^versions'
```

Note the Magento version from the third command (for example `2.4.8-p5`). The fourth lists which of the packages below are installed, and the fifth prints this package's version if it is already there. Then pick the first row that matches:

| What you found | What to do |
|---|---|
| `composer show magento/magento2-base` failed | Stop. This is not a Magento project, or not its root directory. |
| `mage-os/framework` | Stop. Mage-OS is not supported, and Composer will refuse the install. Tell the person that Mage-OS ships its own security releases. |
| `magento/product-enterprise-edition` or `magento/extension-b2b` | Stop. This package refuses to install on Adobe Commerce or B2B, because those editions need Adobe's licensed files. Walk the person through [Adobe Commerce and B2B](adobe-commerce-and-b2b.md) instead. |
| Magento before 2.4.2, PHP before 7.4, or Composer before 2.2 | Stop, and say which requirement is not met. |
| `samjuk/m2-meta-security-patches` at a version before `2026.10.09`, or `vaimo/composer-patches` | This is an upgrade from the releases that used vaimo. Follow steps 2 to 5, using the upgrade command in step 3. |
| `samjuk/m2-meta-security-patches` at `2026.10.09` or later | It is already installed. Go to step 4. |
| None of the above | A fresh install. Follow steps 2 to 5. |

## 2. Configure Composer

Read `extra.magento-patches.trust` in `composer.json` first. If it does not exist, run both commands:

```bash
composer config --no-plugins allow-plugins.samjuk/magento-patch-installer true
composer config --json extra.magento-patches.trust '["samjuk/m2-meta-security-patches"]'
```

If `trust` already lists other packages, run only the first command, and add `"samjuk/m2-meta-security-patches"` to the existing list by editing `composer.json`. The second command replaces the list. If the list contains `"samjuk/*"` from earlier instructions, suggest replacing it with the package name.

On an upgrade, both lines have to be in place before the update in step 3. Without them the update stops partway, with Magento's root files not deployed.

## 3. Install or upgrade

A fresh install:

```bash
composer require samjuk/m2-meta-security-patches:">=2026.02.01"
```

An upgrade from the vaimo releases: check the constraint on `samjuk/m2-meta-security-patches` in `composer.json`. If it would not allow `2026.10.09` or later (an exact version such as `2026.09.08`, for example), ask the person before changing it to `>=2026.02.01`. Then:

```bash
composer update samjuk/m2-meta-security-patches --with-all-dependencies
```

The update removes vaimo and reverts its patches on the way out, before the new installer applies them again. If the project's own `composer.json` requires `vaimo/composer-patches`, it may carry other patches: leave it, and mention it to the person.

Expect the Composer run to end with a "Magento security patches" summary and exit `0`. If an upgrade stopped partway, run `composer reinstall magento/magento2-base`. That puts Magento's root files back, and the installer applies everything on the same run.

## 4. Check the result

```bash
composer magento-patches:status
composer magento-patches:verify; echo "exit code: $?"
```

| Exit code | Meaning | What to do |
|---|---|---|
| `0` | Every patch for this store is in place | Report it. |
| `1` | A patch is missing | Run `composer magento-patches:apply`, then verify again. |
| `2` | A patch conflicts with the files on disk | Stop. Run `composer magento-patches:status -v` and show the person the files it names. |
| `3` | The configuration is wrong | Stop. Show the person the error. |

A conflict usually means a core file was changed locally, or another tool patched it differently. Do not resolve it by editing files, deleting the state file or skipping the patch. The person decides.

Monthly patches only apply to the newest patch release of each Magento line. If `status` warns that the store is behind (`magento/magento2-base is on 2.4.8-p4, but patches here are built for 2.4.8-p5`), tell the person that they will apply once Magento is upgraded, and that the out-of-band hotfixes that cover the store still apply now. An end-of-life warning in `status` is worth passing on as well.

## 5. Suggest a deploy check

Ask before you edit any CI or deploy configuration. Suggest adding this as its own step, after `composer install`:

```bash
composer magento-patches:verify --no-interaction
```

It has to be a separate step. `composer install --no-plugins`, or a plugin refused in `allow-plugins`, installs everything and exits `0` without applying a patch, and a plugin that never ran cannot report it.

## When the person wants more

- **Switch a patch off:** skip it in their own `composer.json`, with a written reason, as shown in [Switching a patch off](usage.md#switching-a-patch-off). Never remove a patch from `vendor/`.
- **Add a patch of their own to one store:** declare it in the project's `composer.json` with `depends` naming what it builds on. See [Declaring Patches](https://github.com/SamJUK/magento-patch-installer/blob/master/docs/declaring-patches.md) and [Extended support](extended-support.md).
- **Add Adobe's restricted months, or patch several stores:** suggest a private package of their own that requires this one, kept in a private repository. See [Extended support](extended-support.md#several-stores-a-package-of-your-own). The files come from Adobe with the person's own repo.magento.com keys. Check each one's sha256 against Adobe's public registry, and keep it unmodified.

## Report back

When you finish, tell the person:

- the Magento version, and what `magento-patches:status` says is covered
- the exit code of `magento-patches:verify`
- the changes you made to `composer.json`
- whether the deploy check is in place
- anything you stopped on, and why
