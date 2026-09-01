#!/usr/bin/env bash
#
# Build the site from the documents
# and refuse the result if it differs from what is committed.
#
# What is deployed has to be what was reviewed.
# A push to `main` republishes the site by fetching the documents,
# so without this it would publish whatever Google Docs said at that moment:
# a sentence someone was still editing,
# or a paragraph deleted an hour ago and not yet restored.
#
# A build is deterministic, so unchanged documents rewrite the committed files
# byte for byte and there is no diff.
# `doc.json` covers the text and `images.json` covers the pictures,
# which are not committed themselves but whose hashes are.

set -euo pipefail

# GitHub renders this as an annotation on the run;
# a terminal renders it as what it says.
fail() {
    if [[ -n ${GITHUB_ACTIONS:-} ]]; then
        echo "::error::$1" >&2
    else
        echo "$1" >&2
    fi
    exit 1
}

# The build writes into `site/`, so anything uncommitted there is about to be lost.
# Against `HEAD` rather than the index,
# so staged-but-not-committed counts as uncommitted, which it is.
if ! git diff --quiet HEAD -- site; then
    fail "site/ has uncommitted changes and this rebuilds into it; commit or stash them first"
fi

uv run eta-publish

# The whole diff, not a summary:
# it is the change to a published report,
# and reading it is the review the commit stands for.
if ! git diff --quiet HEAD -- site; then
    git diff --stat HEAD -- site >&2
    git diff HEAD -- site >&2
    fail "the documents have changed since site/ was committed; \
read the diff above, and commit the rebuilt files now in the working tree"
fi

echo "site/ is what a fresh build writes"
