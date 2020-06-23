#!/usr/bin/env bash

export CODE_TESTS_PATH="$(pwd)/language-server/client/out/test"
export CODE_TESTS_WORKSPACE="$(pwd)/language-server/client/testFixture"

node "$(pwd)/language-server/client/out/test/runTest"