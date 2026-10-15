# Included patches

Two kinds: Adobe's monthly isolated patches, and out-of-band hotfixes for vulnerabilities that could not wait. All of them are Community Edition patches. For Adobe Commerce and B2B, see [Adobe Commerce and B2B](adobe-commerce-and-b2b.md).

## Monthly isolated patches

An isolated patch is Adobe's term for a security fix shipped on its own rather than in a full patch release. Isolated does not mean independent: **each month is built on the one before, and they have to be applied in order.** Each base version's months are declared as one chain in [`patches/isolated/patches.json`](../patches/isolated/patches.json), and the installer refuses to apply a month whose predecessor is missing.

Each month is built against the newest patch release of its line when it came out, and only applies to that one. `2026-07-001` for 2.4.8 applies to 2.4.8-p5, not p4 or earlier. If you are behind, upgrade first.

| Patch | 2.4.9 | 2.4.8-p5 | 2.4.7-p10 | 2.4.6-p15 |
|---|---|---|---|---|
| `2026-07-001` July 2026 | ✓ | ✓ | ✓ | ✓ |
| `2026-08-001` August 2026 | ✓ | ✓ | ✓ | ✓ |
| `2026-09-001` September 2026 | ✓ | ✓ | ✓ | ✓ |
| `2026-10-001` October 2026 | ✓ | ✓ | ✓ | Commerce only |
| `2026-10-002` October 2026, second | | ✓ | | |

`2026-10-002` exists for 2.4.8-p5 only. Adobe split the `EmailAddress.php` fix (CVE-2026-91013) out of its October patch for that line; the 2.4.7-p10 and 2.4.9 October patches already contain it.

**Why does 2.4.6-p15 stop at September?** Adobe restricts its October file for 2.4.6-p15 to Adobe Commerce licence holders, so a public package cannot ship it. Files that were public when released stay here even if Adobe restricts them later. If you hold a licence, you can add October yourself on top of this package's chain: see [Extended support](extended-support.md).

## Out-of-band hotfixes

Declared in [`patches/emergency/patches.json`](../patches/emergency/patches.json), each for the versions it affects.

| Hotfix | What it fixes | Applies to |
|---|---|---|
| APSB26-146, StyleSmuggler (VULN-39341) | CVE-2026-75650: unauthenticated remote code execution through GraphQL style properties rendered in admin email previews. Exploited in the wild, CVSS 10.0 | 2.4.9, 2.4.8-p5, 2.4.7-p10, 2.4.6-p15 |
| APSB25-94, Polyshell | The Polyshell vulnerability | Everything before 2.4.9 |
| CVE-2025-54236, Session Reaper | A session security vulnerability | 2.4.8-p2, 2.4.7-p7, 2.4.6-p12, 2.4.5-p14 and earlier in each line |
| CVE-2024-34102, CosmicSting | CosmicSting | 2.4.7, 2.4.6-p5, 2.4.5-p7, 2.4.4-p8 and earlier in each line |

Hotfixes are not part of the monthly chain. Adobe ships them to apply alongside it.

## Check the files yourself

None of Adobe's files are changed. Every file in `patches/isolated/`, and every `VULN-*` file in `patches/emergency/`, is Adobe's byte for byte, and its sha256 is the one Adobe publishes in its patch registry:

```sh
curl -s https://repo.magento.com/patch/patch-registry.json | jq -r '.patches["249-2026-08-001-CE"].sha256'
shasum -a 256 vendor/samjuk/m2-meta-security-patches/patches/isolated/2026-08-001/2.4.9-CE.patch
```

Registry ids are the version without its dots or hyphens, then the patch id, then `-CE`: 2.4.8-p5's October patch is `248p5-2026-10-001-CE`, and its StyleSmuggler hotfix `248p5-VULN-39341-CE`.

Releases up to `2026.09.11-beta2` changed two things to suit `vaimo/composer-patches`: hunks for project root files pointed at `vendor/magento/magento2-base/`, and the `vendor/bin/patch-status` hunks were removed. The current installer needs neither, and both are gone.
