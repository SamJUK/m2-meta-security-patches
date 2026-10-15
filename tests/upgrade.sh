#!/usr/bin/env bash
# Copyright (c) 2026 Sam James. Licensed under the Open Software License version 3.0.
# SPDX-License-Identifier: OSL-3.0
#
# A store on a release from Packagist updates the way the README says, then keeps
# running Composer. tests/test.sh covers fresh installs of the working tree.
#
#   bash tests/upgrade.sh <magento-version>             e.g. 2.4.9, 2.4.8-p5
#
#   FROM=latest|<tag>|none   where the store starts: the newest release below TO
#                            (default), a release tag, or nothing (fresh install)
#   TO=working|<tag>         what it updates to: this working tree (default), or a
#                            release on Packagist, to check one after it ships
#   INSTALLER=<path>         offer a local samjuk/magento-patch-installer checkout
#
# The runs after the update matter as much as the update itself: a month that
# rewrites an earlier month's lines used to apply cleanly once and fail every
# run after.

set -euo pipefail

CWD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$CWD")"
VERSION="${1:?usage: $0 <magento-version>}"
FROM="${FROM:-latest}"
TO="${TO:-working}"
PKG=samjuk/m2-meta-security-patches
IMAGE=$(jq -r --arg v "$VERSION" 'to_entries[] | select(.value[$v]) | "\(.key):\($v)-\(.value[$v])"' "$CWD/matrix.json" | head -1)
[ -n "$IMAGE" ] || { echo "no image for $VERSION in tests/matrix.json"; exit 1; }

if [ "$FROM" = latest ]; then
    # Date versions sort as strings. -pN releases are stable; betas are not.
    FROM=$(curl -sf "https://repo.packagist.org/p2/$PKG.json?$(date +%s)" | jq -r --arg to "$TO" '
        [.packages[][] | .version | select(test("^[0-9.]+(-p[0-9]+)?$"))
            | select($to == "working" or . < $to)] | sort | last // empty')
    [ -n "$FROM" ] || { echo "no release on Packagist to start from"; exit 1; }
fi

NAME="m2-meta-upgrade-$(echo "$VERSION-$FROM" | tr '.' '-')"
WORK=$(mktemp -d)
trap 'docker rm -f "$NAME" >/dev/null 2>&1; rm -rf "$WORK"' EXIT

# Nothing mounts at the image's ./extensions path repo, which is canonical and
# would hide Packagist's releases of this package.
MOUNTS=()
if [ "$TO" = working ]; then
    # Versioned above every release, so the README's constraint picks it up.
    EXPECT=9999.12.31
    mkdir "$WORK/next"
    tar -C "$ROOT" --exclude=.git -cf - . | tar -C "$WORK/next" -xf -
    jq --arg v "$EXPECT" '.version = $v' "$ROOT/composer.json" > "$WORK/next/composer.json"
    MOUNTS+=(-v "$WORK/next:/next:ro")
else
    EXPECT="$TO"
fi
[ -n "${INSTALLER:-}" ] && MOUNTS+=(-v "$(cd "$INSTALLER" && pwd):/installer:ro")

docker run -d --platform linux/amd64 --name "$NAME" ${MOUNTS[@]+"${MOUNTS[@]}"} "$IMAGE" >/dev/null

# Passes on the marker, not the exit code: a docker exec client killed while the
# daemon hangs exits 0.
step() {
    docker exec "$NAME" sh -c "cd /var/www/html && ($2) && echo __STEP_OK__" >"$WORK/out" 2>&1 || true
    if grep -qx '__STEP_OK__' "$WORK/out"; then
        echo "✅ $1"
    else
        echo "❌ $1"
        tail -40 "$WORK/out"
        exit 1
    fi
}

# The images list vaimo in root require-dev; a stock store does not, and with -W
# vaimo 6.0.2 -> 6.0.3 mid-run fatals on its own half-replaced classes.
step "configure like a stock store" "if php -r 'exit(isset(json_decode(file_get_contents(\"composer.json\"), true)[\"require-dev\"][\"vaimo/composer-patches\"]) ? 0 : 1);'; \
        then composer remove --dev vaimo/composer-patches --no-interaction; fi \
    && composer config --json extra.magento-patches.trust '[\"samjuk/*\"]' \
    && composer config --no-plugins allow-plugins.samjuk/magento-patch-installer true \
    && composer config --no-plugins allow-plugins.vaimo/composer-patches true"

if [ -n "${INSTALLER:-}" ]; then
    # Versioned inside the working tree's constraint (^0.3 becomes 0.3.999) and
    # not canonical, so a release on an older constraint still gets Packagist's
    # installer, and the update moves to the local one.
    LOCAL=$(jq -r '.require["samjuk/magento-patch-installer"]' "$ROOT/composer.json" | sed -E 's/^[^0-9]*([0-9]+\.[0-9]+).*/\1.999/')
    step "offer the local installer as $LOCAL" "cp -r /installer /installer-copy && rm -rf /installer-copy/vendor \
        && php -r '\$f=\"/installer-copy/composer.json\"; \$j=json_decode(file_get_contents(\$f),true); \$j[\"version\"]=\"$LOCAL\"; file_put_contents(\$f, json_encode(\$j, JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES));' \
        && composer config repositories.installer '{\"type\": \"path\", \"url\": \"/installer-copy\", \"canonical\": false}'"
fi

if [ "$FROM" != none ]; then
    # No -W: a store adds the package without updating what it already has.
    step "install $FROM from Packagist" "composer require $PKG:$FROM --no-interaction"
    step "$FROM is patched" "if composer show samjuk/magento-patch-installer >/dev/null 2>&1; \
        then composer magento-patches:verify --no-interaction; \
        else composer patch:list --status applied --no-interaction; fi"
fi

if [ "$TO" = working ]; then
    step "offer the working tree as $EXPECT" "composer config repositories.next \
        '{\"type\": \"path\", \"url\": \"/next\", \"canonical\": false, \"options\": {\"symlink\": false}}'"
fi

step "update to $EXPECT, as the README says" "composer require '$PKG:>=2026.02.01' --no-update --no-interaction \
    && composer update $PKG --no-interaction -W"
step "installed $EXPECT" "composer show $PKG | grep -qE '^versions : \* $EXPECT\$'"
step "verify after the update" "composer magento-patches:verify --no-interaction"
# verify exits 0 on an empty set, so a wrong include path would pass silently.
step "patches are declared" "composer magento-patches:list --json --no-interaction \
    | php -r 'exit(count(json_decode(stream_get_contents(STDIN), true)[\"patches\"] ?? []) > 0 ? 0 : 1);'"
step "the next composer install succeeds" "composer install --no-interaction"
step "and still verifies" "composer magento-patches:verify --no-interaction"
step "a further apply writes nothing" "out=\$(composer magento-patches:apply --no-interaction 2>&1) \
    && ! echo \"\$out\" | grep -E '^ +(applied|superseded) '"
step "reinstalling magento2-base heals" "base=\$(composer show -N | awk '\$1 ~ /\\/magento2-base\$/ { print \$1; exit }') \
    && composer reinstall \$base --no-interaction && composer magento-patches:verify --no-interaction"
step "a fresh vendor comes back patched" "rm -rf vendor && composer install --no-interaction \
    && composer magento-patches:verify --no-interaction"
step "dump-autoload keeps it patched" "composer dump-autoload --no-interaction \
    && composer magento-patches:verify --no-interaction"

# Detection proves the lines are on disk, not that the file still parses. A hunk
# applied twice reads as applied, and only php -l notices.
step "patched PHP files still parse" "files=\$(cd vendor/$PKG/patches \
        && cat isolated/*/$VERSION-CE.patch emergency/*/$VERSION.patch 2>/dev/null \
        | sed -nE 's#^\\+\\+\\+ b/(.*\\.php)\$#\\1#p' | sort -u) \
    && for f in \$files; do [ ! -f \"\$f\" ] || php -l \"\$f\" >/dev/null || exit 1; done"

docker exec "$NAME" sh -c "cd /var/www/html && composer show samjuk/magento-patch-installer | grep -E '^versions' \
    && composer magento-patches:status --no-interaction" || true
