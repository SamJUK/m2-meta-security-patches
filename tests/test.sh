#!/usr/bin/env bash
# A simple bash script to test install the composer package across a range of Magento versions

set -euo pipefail

CWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CLR_RESET='\033[0m'
CLR_RED='\033[1;31m'
CLR_YELLOW='\033[1;33m'
CLR_GREEN='\033[1;32m'
CLR_GREY='\033[0;30m'

usage() {
    echo "Usage: $0 [--summary] [package] [app-version] [php-version]"
    echo
    echo "Options:"
    echo "  --summary            Show summary of test results"
    echo "  package              The composer package to test"
    echo "  app-version          The Magento/MageOS version to test against"
    echo "  php-version          The PHP version to test against"
    exit 1
}


POSITIONAL=()
SUMMARY=false
for arg in "$@"; do
    if [ "$arg" == "--summary" ]; then
        SUMMARY=true
    else
        POSITIONAL+=("$arg")
    fi
done

test_configuration() {
    local PACKAGE=$1
    local APP_VERSION=$2
    local PHP_VERSION=$3

    CONTAINER_IMAGE="$PACKAGE:$APP_VERSION-$PHP_VERSION"
    CONTAINER_NAME=$(echo "test-m2-meta-security-patches-$CONTAINER_IMAGE" | sed 's/[^a-zA-Z0-9]/_/g' | tr '[:upper:]' '[:lower:]')
    trap 'docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true' EXIT
    
    set +e
    DOCKER_START_OUTPUT=$(docker run -d --platform linux/amd64 --name "$CONTAINER_NAME" -v "$CWD/../:/var/www/html/extensions/m2-meta-security-patches:ro" $CONTAINER_IMAGE 2>&1)

    if [ "$?" -ne 0 ]; then
        echo -e "⚠️ ${CLR_YELLOW}Failed to start container for configuration: Package=$PACKAGE, App Version=$APP_VERSION, PHP Version=$PHP_VERSION"
        if [ "$SUMMARY" = false ]; then
            echo "---- Docker Start Output Start ----"
            echo "$DOCKER_START_OUTPUT" | sed "s/^/\[$APP_VERSION $PHP_VERSION\] /" | sed "s/\x1b\[[0-9;]*m//g"
            echo "---- Docker Start Output End ----"
            echo -e "${CLR_RESET}"
            exit 1
        fi
        echo -e "${CLR_RESET}"
    fi

    TEST_OUTPUT=$(docker exec "$CONTAINER_NAME" sh -c "composer require samjuk/m2-meta-security-patches:@dev --no-interaction -W -vvv" 2>&1)
    if [ "$?" -ne 0 ]; then
        echo -e "❌ ${CLR_RED}Test failed for configuration: Package=$PACKAGE, App Version=$APP_VERSION, PHP Version=$PHP_VERSION${CLR_GREY}"
        if [ "$SUMMARY" = false ]; then
            echo "---- Test Output Start ----"
            echo "$TEST_OUTPUT" | sed "s/^/\[$APP_VERSION $PHP_VERSION\] /" | sed "s/\x1b\[[0-9;]*m//g"
            echo "---- Test Output End ----"
            echo -e "${CLR_RESET}"
            exit 1
        else
            echo "$TEST_OUTPUT" | sed "s/^/\[$APP_VERSION $PHP_VERSION\] /" | sed "s/\x1b\[[0-9;]*m//g" | tail -n8
        fi
        echo -e "${CLR_RESET}"
    else
        echo -e "✅ ${CLR_GREEN}Test succeeded for configuration: Package=$PACKAGE, App Version=$APP_VERSION, PHP Version=$PHP_VERSION${CLR_RESET}"
    fi

    docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
    trap - EXIT

    set -e
}


if [ ${#POSITIONAL[@]} -eq 3 ]; then
    test_configuration "${POSITIONAL[0]}" "${POSITIONAL[1]}" "${POSITIONAL[2]}"
    exit 0
elif [ ${#POSITIONAL[@]} -ne 0 ]; then
    usage
fi

# Test Matrix should start at the newest versions and work its way down
TEST_MATRIX_FILE="$CWD/matrix.json"
[ -f "$TEST_MATRIX_FILE" ] || {
    echo "Test matrix file: $TEST_MATRIX_FILE not found!"
    exit 1
}

TEST_MATRIX=$(cat "$TEST_MATRIX_FILE")
for PACKAGE in $(echo "${TEST_MATRIX}" | jq -r 'keys[]'); do
    for APP_VERSION in $(echo "${TEST_MATRIX}" | jq -r --arg pkg "$PACKAGE" '.[$pkg] | keys[]' | sort -rV); do
        PHP_VERSION=$(echo "${TEST_MATRIX}" | jq -r --arg pkg "$PACKAGE" --arg ver "$APP_VERSION" '.[$pkg][$ver]')
        test_configuration "$PACKAGE" "$APP_VERSION" "$PHP_VERSION"
    done
done

echo -e "${CLR_GREEN}All tests completed successfully!${CLR_RESET}"