# Extended support

2.4.6 reached end of life on 11th August 2026, and Adobe still patches it. From October 2026 its monthly patches go to Adobe Commerce licence holders only, as every 2.4.4-p18 and 2.4.5-p17 monthly patch in Adobe's registry does. The registry marks them `"entitlements": ["ee"]`, and downloading one without a licence gets a login page. (It has since marked September's 2.4.6-p15 file the same way. That one was public when Adobe released it, so it stays here.)

This package only ships files that were public when Adobe released them, so it stops where the restriction starts:

| Magento | Monthly patches here | Restricted |
|---|---|---|
| 2.4.6-p15 | July to September 2026 | October 2026 onwards |
| 2.4.5-p17 | none | every month |
| 2.4.4-p18 | none | every month |

If you hold a licence, you can add the restricted months yourself and keep this package's ordering and checks. That needs samjuk/magento-patch-installer 0.3 or later, which lets your patch build on one in this package (`composer show samjuk/magento-patch-installer` shows yours).

## Get the file

Download it from Adobe with your repo.magento.com keys, the same pair as in your `auth.json`, and check its sha256 against the registry:

```sh
curl -fsSL -u "$PUBLIC_KEY:$PRIVATE_KEY" -o patches/246p15-2026-10-001-CE.diff \
    https://repo.magento.com/patch/246p15-2026-10-001-CE.diff
curl -s https://repo.magento.com/patch/patch-registry.json | jq -r '.patches["246p15-2026-10-001-CE"].sha256'
shasum -a 256 patches/246p15-2026-10-001-CE.diff
```

The registry is public and lists the sha256 of restricted files too, so a copy from anywhere else can be checked the same way. Keep the file unmodified.

## One store: your project's composer.json

Declare the month on the same line as this package's chain, and name what it builds on:

```json
"extra": {
    "magento-patches": {
        "trust": ["samjuk/*"],
        "lines": {
            "2.4.6-p15": {
                "base": { "magento/magento2-base": "2.4.6-p15" },
                "patches": [
                    {
                        "id": "2026-10-001",
                        "label": "October Isolated",
                        "source": "patches/246p15-2026-10-001-CE.diff",
                        "depends": ["2026-09-001", "APSB26-146"]
                    }
                ]
            }
        }
    }
}
```

`depends` names every patch in this package that yours overlaps: September, and the StyleSmuggler hotfix, which changes two of the same files and is not part of the monthly chain. Leave one out and the installer refuses your patch, with an error naming each patch it overlaps.

Each month, add the new file with `depends` on the month before it, and on anything else the installer names.

## Several stores: a package of your own

Put the files in a private package that requires this one:

```
acme/magento-licensed-patches
├── composer.json
└── patches/
    └── 246p15-2026-10-001-CE.diff
```

```json
{
    "name": "acme/magento-licensed-patches",
    "type": "library",
    "require": {
        "samjuk/magento-patch-installer": "^0.3",
        "samjuk/m2-meta-security-patches": ">=2026.10.09"
    },
    "extra": {
        "magento-patches": {
            "lines": {
                "2.4.6-p15": {
                    "base": { "magento/magento2-base": "2.4.6-p15" },
                    "cumulative": true,
                    "patches": [
                        {
                            "id": "2026-10-001",
                            "label": "October Isolated",
                            "source": "patches/246p15-2026-10-001-CE.diff"
                        }
                    ]
                }
            }
        }
    }
}
```

Requiring this package is what puts yours on top of it: a package's patches apply after those of the packages it requires, and are checked as built on the ones they share a file with. No `depends` needed. Each month, append the new file to the list: `cumulative` makes the order you list them the order they apply.

Then in each store, trust it alongside this one and require it:

```sh
composer config --json extra.magento-patches.trust '["samjuk/*", "acme/*"]'
composer require acme/magento-licensed-patches
```

A private Git repository used as a Composer `vcs` repository is enough to host it. Each store still needs its own Adobe Commerce licence: the package shares the work of keeping the files current, not the licence.

To stop using it, take its patches off before removing it, or the months beneath them read as conflicts: see [removing a package that builds on another](https://github.com/SamJUK/magento-patch-installer#patches-from-several-sources).

## What about 2.4.4 and 2.4.5?

There is no monthly chain here for those lines to build on, so declare the whole chain yourself, as a `cumulative` line like the [Adobe Commerce example](adobe-commerce-and-b2b.md#how-do-i-patch-an-adobe-commerce-store). This package still applies Polyshell to both. Its StyleSmuggler hotfix is only for 2.4.6-p15 and later, but Adobe's StyleSmuggler files for 2.4.4-p18 and 2.4.5-p17 are public, so add those as well.

## What we have tested

Both layouts above, on a 2.4.6-p15 store with Adobe's real October file. Both applied all 22 files on top of September, and the store stayed clean through a further install, a package reinstall and a fresh `vendor/`. Leaving `depends` out of the project's `composer.json` got the patch refused, leaving this package's patches in place.

We have not tested 2.4.4 or 2.4.5.
