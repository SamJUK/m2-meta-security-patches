#!/usr/bin/env bash
# Copyright (c) 2026 Sam James. Licensed under the Open Software License version 3.0.
# SPDX-License-Identifier: OSL-3.0
#
# Every patch file must match Adobe's registry sha256, or the pin in
# patches/SHA256SUMS for the few hotfixes the registry does not list.
# A file that is neither fails: nothing ships unchecked.
#
#   bash bin/check-patch-hashes.sh
set -euo pipefail

DIR=$(cd "$(dirname "$0")/../patches" && pwd)
PINS="$DIR/SHA256SUMS"
REGISTRY=$(curl -sfS https://repo.magento.com/patch/patch-registry.json)

failed=0
while IFS= read -r file; do
    rel=${file#"$DIR"/}
    have=$(shasum -a 256 "$file" | cut -d' ' -f1)

    # isolated/2026-10-001/2.4.8-p5-CE.patch -> 248p5-2026-10-001-CE
    # emergency/VULN-39341/2.4.8-p5.patch    -> 248p5-VULN-39341-CE
    id=
    if [[ $rel =~ ^isolated/([0-9]{4}-[0-9]{2}-[0-9]{3})/([0-9.]+(-p[0-9]+)?)-CE\.patch$ ]]; then
        id="${BASH_REMATCH[2]//[.-]/}-${BASH_REMATCH[1]}-CE"
    elif [[ $rel =~ ^emergency/(VULN-[0-9]+)/([0-9.]+(-p[0-9]+)?)\.patch$ ]]; then
        id="${BASH_REMATCH[2]//[.-]/}-${BASH_REMATCH[1]}-CE"
    fi

    want=
    if [[ -n $id ]]; then
        want=$(jq -r --arg id "$id" '.patches[$id].sha256 // empty' <<<"$REGISTRY")
        source="registry $id"
    fi
    if [[ -z $want ]]; then
        want=$(awk -v f="$rel" '$2 == f { print $1 }' "$PINS")
        source="SHA256SUMS"
    fi

    if [[ -n $want && ! $want =~ ^[0-9a-f]{64}$ ]]; then
        echo "::error file=patches/$rel::$source has a malformed sha256"
        failed=1
    elif [[ -z $want ]]; then
        echo "::error file=patches/$rel::not in Adobe's registry or patches/SHA256SUMS"
        failed=1
    elif [[ $have != "$want" ]]; then
        echo "::error file=patches/$rel::sha256 $have does not match $source ($want)"
        failed=1
    else
        echo "ok  $rel ($source)"
    fi
done < <(find "$DIR" -type f ! -name '*.json' ! -name SHA256SUMS ! -name .gitkeep | sort)

exit $failed
