# Adobe Commerce and B2B

This package is Community Edition only. Its `composer.json` conflicts with `magento/product-enterprise-edition` and `magento/product-b2b-edition`, so Composer refuses to install it on an Adobe Commerce or B2B store. Two reasons:

- **The files are Adobe's to distribute.** Adobe patches those editions with extra files that contain Adobe Commerce code. They download from Adobe today, but that does not make them a public package's to redistribute.
- **Half the patches would look like all of them.** The Community Edition patches here apply cleanly to the code the editions share. On their own they would report an Adobe Commerce store as fully patched while its Commerce code went untouched.

What we recommend instead is the same tooling, with your own copy of Adobe's files.

## What does Adobe publish for those editions?

Adobe's [patch registry](https://repo.magento.com/patch/patch-registry.json) sorts patches into areas:

- **CE** applies to every store.
- **EE** adds patches for stores with `magento/product-enterprise-edition`.
- **B2B** adds patches for stores with `magento/extension-b2b`, numbered by the B2B extension's own versions (`1.5.3`), not Magento's.

So an Adobe Commerce store needs the CE months *and* the EE months for its version, and a B2B store needs the B2B months as well. Each area is its own chain: the 2.4.9 EE patch for October 2026 requires the EE patches for July and August (there was no EE patch for September), not the CE ones. The 2.4.9 EE files we checked only touch Adobe Commerce modules (staging, gift cards, customer attributes), so they sit beside the CE files rather than replacing them.

## How do I patch an Adobe Commerce store?

Use [samjuk/magento-patch-installer](https://github.com/SamJUK/magento-patch-installer) directly. It is what this package runs on, so you get the same ordering, the same check on every Composer run, and the same healing after a package reinstall.

1. Require it and let it run:

    ```bash
    composer config --no-plugins allow-plugins.samjuk/magento-patch-installer true
    composer require samjuk/magento-patch-installer
    ```

2. Download Adobe's CE and EE files for your version from `https://repo.magento.com/patch/<file_name>`, using your own repo.magento.com credentials. Check each one's sha256 against the registry entry, as [this package does](patches.md#check-the-files-yourself). Keep them unmodified, in a directory of their own (`patches/` often exists already in a Magento project).

3. Declare them. One manifest per area keeps the chains apart. The CE months form a cumulative line, where the order listed is the order applied. The EE months name what each is built on, because they are not built on the CE months:

    ```json
    "extra": {
        "magento-patches": {
            "include": ["adobe-patches/ce/patches.json", "adobe-patches/ee/patches.json"]
        }
    }
    ```

    `adobe-patches/ce/patches.json`:

    ```json
    {
        "lines": {
            "2.4.9": {
                "base": { "magento/magento2-base": "2.4.9" },
                "cumulative": true,
                "patches": [
                    { "id": "2026-07-001", "source": "249-2026-07-001-CE.patch" },
                    { "id": "2026-08-001", "source": "249-2026-08-001-CE.patch" },
                    { "id": "2026-09-001", "source": "249-2026-09-001-CE.patch" },
                    { "id": "2026-10-001", "source": "249-2026-10-001-CE.patch" }
                ]
            }
        },
        "patches": [
            { "id": "APSB26-146", "label": "StyleSmuggler", "source": "VULN-39341-249.patch", "base": { "magento/magento2-base": "2.4.9" } }
        ]
    }
    ```

    `adobe-patches/ee/patches.json`:

    ```json
    {
        "lines": {
            "2.4.9": {
                "base": { "magento/magento2-base": "2.4.9" },
                "patches": [
                    { "id": "2026-07-001-EE", "source": "249-2026-07-001-EE.diff" },
                    { "id": "2026-08-001-EE", "source": "249-2026-08-001-EE.diff", "depends": ["2026-07-001-EE"] },
                    { "id": "2026-10-001-EE", "source": "249-2026-10-001-EE.diff", "depends": ["2026-08-001-EE"] }
                ]
            }
        }
    }
    ```

    An id has to be unique within a line, which is why the EE months carry an `-EE` suffix. B2B months go in a third manifest, on a line for your B2B version with a `base` on `magento/extension-b2b`.

4. Run `composer magento-patches:verify` in your deploy pipeline, as [any store should](usage.md#in-a-deploy-pipeline).

Each month, append the new files to the end of their lists. Adobe publishes on the second Tuesday.

**What we have tested.** The layout above, with Adobe's real CE and EE files for 2.4.9, installs, applies the CE chain, orders the EE chain correctly, and stays clean on the runs after. We ran it on a Community Edition store, where the EE files' targets read as "not covered". We have no licensed Adobe Commerce or B2B store to test against, so the EE and B2B patches themselves have not been applied by us.

## What about several stores?

Put the same files and manifests in a private Composer package, and trust it in each store by name:

```bash
composer config --json extra.magento-patches.trust '["your-vendor/*"]'
```

A private Git repository used as a Composer `vcs` repository is enough. Private Packagist, Satis and GitLab's package registry work too; GitHub Packages does not support Composer.

Each store still needs its own Adobe Commerce licence. A private package is a way to share the work of keeping the files current, not a licence. We are not lawyers, so check your agreement with Adobe.
