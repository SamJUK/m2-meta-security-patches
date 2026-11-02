# Maintaining

Patch day, by hand or by a coding agent.

Adobe publishes isolated patches on the second Tuesday of the month, listed in a public registry (`repo.magento.com/patch/patch-registry.json`). This brings them in **unmodified**, tests them, and stops at `git add`. The maintainer reviews, commits, raises the PR and tags.

Never edit an Adobe patch file. Never commit, push or tag unless the maintainer asks: patch day stops at `git add`. Stop and report rather than work around anything under **Decisions** below.

## 1. Start clean

The **Adobe patch sync** workflow (`.github/workflows/adobe-sync.yml`) runs this fetch nightly and opens a pull request from `bot/adobe-patches`, with the test matrix already run on it. Check for one first:

```bash
git status --short   # nothing
gh pr view bot/adobe-patches --json url,state,body
```

If it is open, do not fetch again: check it out (`gh pr checkout bot/adobe-patches`), read its body for what was added and what needs a decision, then go straight to **3. Test** for anything the matrix did not cover, and **4. Document**.

Otherwise, start a branch and fetch by hand:

```bash
git switch master && git pull --ff-only
git switch -c <mon>-isolated   # e.g. oct-isolated, matching earlier PR branches
```

## 2. Fetch

```bash
python3 -I bin/ingest-adobe-patches.py --dry-run
python3 -I bin/ingest-adobe-patches.py
```

For each base line in `patches/isolated/patches.json` it takes the months Adobe has published after the line's last one, checks Adobe's own `requires` says each follows the one before, downloads it, checks the registry's sha256, and appends it to the line. Files are written only if the whole run succeeds. Output is JSON:

- `added` — what was written. Per entry:
  - `rewrites_earlier_months` — files an earlier month also patches. Normal for Adobe's chain (`vendor/bin/patch-status` changes every month); the installer checks the earlier month beneath the later one.
  - `overlaps_emergency_patches` — files an emergency patch for the same line also patches. Not a conflict by itself: October 2026 changed different lines of the same two files as StyleSmuggler, and both applied in either order. The upgrade tests decide. Report the overlap either way, and stop if they fail.
  - `root_or_vendor_bin` — information only. The installer patches both copies of a root file.
- `decisions` — see below. Never resolve these yourself.
- `malformed_registry_entries` — registry entries that failed validation and were ignored. Report them.

Nothing new is a normal answer before patch day. Say so and stop.

## Decisions

Report each one to the maintainer with what you found. Do not act on it.

The nightly sync fails until a decision is recorded. Acknowledging a month that blocks a line (a gated file, a `requires` mismatch) also hides every later month on that line, because the fetch stops there: delete the line again if that month is ever resolved. Once the maintainer has made one, suggest adding the start of the decision's message to `.github/adobe-sync-acknowledged` (usually the registry id; see the file's header for hotfixes) with a dated comment saying what was decided, and include that file in the staged change.

| Message | Meaning |
|---|---|
| `requires [...] but the <line> chain ends at ...` | Adobe's chain disagrees with ours: a month we do not have, or one withdrawn. If the extra id is an emergency patch we already ship for that line (APSB26-146), the maintainer approved moving its entry from `patches/emergency/patches.json` to the line's chain just before the new month, `source` as `../emergency/...`, same id. Then add the month by hand, test, and flag it in the report |
| `HTTP 401 ... gates it to Commerce customers` | Adobe restricts the file to Adobe Commerce licences. A file that was public on release day and gated later stays shipped (2.4.6-p15 September). One gated from release is not shipped: that line stays on its last month, and the changelog says so (decided 2026-10-13) |
| `Adobe lists <line> as Commerce-only` | Same question, for a file that still downloaded |
| `newer than the <line> line` / `new release line` | A new patch release. See **New base version**: not yet seen, so stop |
| `Out-of-band VULN-...` | A hotfix outside the monthly cycle. See **Out-of-band patches** |
| `exists with different content` | Someone edited a patch file in the repo. Never overwrite |

### The sync stops

`Adobe has published more, or changed a file, since the open bot/adobe-patches pull request` means a new month landed, or Adobe re-issued a file, while the pull request was open. Merge it first if it is ready, or copy any docs and changelog commits off it and close it. The next run rebuilds the branch.

## 3. Test

For every line in `added`. PHP versions come from `tests/matrix.json`.

Each run is one container. Measured on 2.4.9: an upgrade run takes about two and a half minutes, peaks around 200 MiB of memory and two to three CPU cores; a fresh install is under half a minute. Each line's image is about 0.9 GB on disk. Check what the Docker host has free (`docker info`, `docker stats --no-stream`) and run as many at once as fit, leaving headroom for whatever else it runs. A container killed for memory looks like a failed test, so when unsure, run fewer.

```bash
bash tests/test.sh samjuk/magento-ci-testing-env <version> <php>   # fresh install
bash tests/upgrade.sh <version>                                    # newest release -> this one
```

`upgrade.sh` installs a release from Packagist, updates to the working tree the way the README tells a store to, then runs the Composer commands a store runs afterwards: verify, install, a further apply that must write nothing, a `magento2-base` reinstall that must heal, and `php -l` on every patched PHP file. The runs *after* the update are where a month that rewrites an earlier month's lines fails. Before an installer release is on Packagist, test against a local checkout:

```bash
INSTALLER=../magento-patch-installer bash tests/upgrade.sh <version>
```

A failure is a finding. Report it with the output. Do not change patches or tests to make it pass. CI runs the full matrix on every pull request (the sync workflow runs it for its own, which GitHub would not otherwise test), so the older patch levels in `tests/matrix.json` need not be run locally.

## 4. Document

- `docs/patches.md`: a row per month in the **Monthly isolated patches** table, ticking each line that got it.
- `README.md`: the coverage table, if a line's last month changed.
- `CHANGELOG.md`, under `## Unreleased`: which months were added, to which lines, and anything a store operator needs to know (a line dropped, a gated file not shipped). The section becomes the release page.

## 5. Stage and report

Stage the month and nothing else: the patch files and manifests, `docs/patches.md`, `README.md`, `CHANGELOG.md`, and `composer.json` or `.github/adobe-sync-acknowledged` if they changed. Leave anything else edited along the way (test harness tweaks, notes, drafts, this file) unstaged, and mention it in the report. Name paths, never `git add -A` or `.`.

```bash
git add patches/ docs/patches.md README.md CHANGELOG.md   # + composer.json, .github/adobe-sync-acknowledged
bash bin/check-patch-hashes.sh   # every file matches the registry or patches/SHA256SUMS
git status --short && git diff --cached --stat
```

Then report, briefly:

1. What Adobe published: registry ids, release date, CVE count per line.
2. What was added, and what was not and why.
3. Test results per version, with the failing output for anything red.
4. Decisions for the maintainer.
5. `Left for you:` review the staged diff, commit, then either push to the sync's pull request or raise one, then release after merge (below).

## Releasing

Only when the maintainer explicitly asks for a release, after the PR is merged and master's CI is green. Releases are made by hand, so the release page needs its credits added here.

The version is the release date; a second release the same day takes `-p1` (`2026.07.14-p1`). `TITLE` follows the earlier pages (`Oct Isolated Patches`, `StyleSmuggler & Sep Isolated Patches`): agree it with the maintainer.

```bash
git switch master && git pull --ff-only
(
set -euo pipefail   # in a subshell: a failed step stops the rest without closing the terminal
V=$(date +%Y.%m.%d)
PREV=$(gh release view --json tagName --jq .tagName)   # the latest release, before this one exists
TITLE=""                                               # agreed with the maintainer
: "${TITLE:?set TITLE first}"
perl -0pi -e "s/^## Unreleased\n/## Unreleased\n\nNothing yet.\n\n## $V — $(date +%F)\n/m" CHANGELOG.md
git commit -m "docs: changelog for $V" CHANGELOG.md && git push
git tag -s "$V" -m "$V" && git push origin "$V"
awk -v h="## $V " 'index($0, h) == 1 {f=1; next} f && /^## / {exit} f' CHANGELOG.md > /tmp/notes.md
who=$(gh api "repos/SamJUK/m2-meta-security-patches/compare/$PREV...$V" --jq '[.commits[] | .author.login // empty | select(endswith("[bot]") | not)] | unique | map("@" + .) | join(", ")')
printf '\n**Contributors:** %s\n\n**Full changelog:** https://github.com/SamJUK/m2-meta-security-patches/compare/%s...%s\n' "$who" "$PREV" "$V" >> /tmp/notes.md
gh release create "$V" --latest --title "$V ($TITLE)" --notes-file /tmp/notes.md
curl -s "https://repo.packagist.org/p2/samjuk/m2-meta-security-patches.json?$(date +%s)" | jq -r '.packages[][0].version'
)
```

If Packagist still shows the old version after a minute, its GitHub grant has lapsed again: reconnect GitHub on the Packagist profile.

Publishing the release starts the **Post-release check** workflow, which installs it from Packagist on every isolated line, fresh and as an update. Check it went green: `gh run list --workflow post-release.yml --limit 1`.

## Out-of-band patches

`VULN-*` hotfixes are added by hand, after the maintainer confirms:

1. The registry entry gives `file_name` and `sha256`. Download `https://repo.magento.com/patch/<file_name>` and check `shasum -a 256`.
2. Save it unmodified as `patches/emergency/VULN-<n>/<line version>.patch`, one per covered line.
3. Declare it in `patches/emergency/patches.json` under `lines.<version>.patches`. The `id` is Adobe's bulletin id (`APSB26-146`), from the KB announcement at `experienceleague.adobe.com/en/docs/commerce-knowledge-base/kb/announcements/commerce-apsb26-<nnn>`. Stores skip patches by id, so a wrong id cannot be fixed later without breaking their config. If the bulletin cannot be found, stop and ask.
4. Add it to the **Out-of-band hotfixes** table in `docs/patches.md`, and to the README coverage table.

A hotfix Adobe does not list in the registry (published only on a KB page, like Polyshell) gets its sha256 in `patches/SHA256SUMS` instead, or the nightly check fails on it: `(cd patches && shasum -a 256 emergency/<file>) >> patches/SHA256SUMS`.

## New base version

To be confirmed: no new patch release has landed since Adobe started isolated patches. The expectation is that one (2.4.8-p6, say) ships with every isolated patch to date already in it. The existing lines would stay as they are, the new release would start a new line with no isolated patches, and the next month's patches would go on top of it.

Until that has happened once, stop and report what Adobe published to the maintainer. A new line also needs its test image in `magento-ci-testing-env` (`docker manifest inspect samjuk/magento-ci-testing-env:<version>-<php>`) and an entry in `tests/matrix.json`.
