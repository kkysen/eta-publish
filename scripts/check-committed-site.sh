#!/usr/bin/env bash
#
# Build the site from the documents and refuse the result if it differs from
# what is committed.
#
# What is deployed has to be what was reviewed. A push to `main` republishes
# the site by fetching the documents, so without this it would publish
# whatever Google Docs said at that moment: a sentence someone was still
# editing, or a paragraph deleted an hour ago and not yet restored.
#
# A build is deterministic, so if the documents have not changed since they
# were committed, it rewrites the committed files byte for byte and there is
# no diff. `doc.json` covers the text and `images.json` covers the pictures,
# which are not committed themselves but whose hashes are.
#
# This is one script rather than a workflow step and a hook that agree,
# because two copies of a rule about what may be published is one copy too
# many. The workflow runs it before deploying, where failing publishes
# nothing and keeps the previous deploy up. The pre-push hook runs it on the
# way out, where failing costs a minute instead of a red workflow.
#
# Usage: check-committed-site.sh [DOC]
#
# `DOC` builds one document on its own, for a report that is not in
# `reports.toml` yet. Without it, every report on the list is built.

set -euo pipefail

doc="${1:-}"

# GitHub renders this as an annotation on the run; a terminal renders it as
# what it says.
fail() {
    if [[ -n ${GITHUB_ACTIONS:-} ]]; then
        echo "::error::$1" >&2
    else
        echo "$1" >&2
    fi
    exit 1
}

# The build writes into `site/`, so anything uncommitted there is about to
# be written over, and the check is about what is committed either way.
# Against `HEAD` rather than against the index, so that staged-but-not-
# committed counts as uncommitted, which it is.
if ! git diff --quiet HEAD -- site; then
    fail "site/ has uncommitted changes and this rebuilds into it; commit or stash them first"
fi

if [[ -n $doc ]]; then
    uv run eta-publish "$doc" -o site
else
    uv run eta-publish -o site
fi

# The whole diff, not a summary of it: it is the change to a published
# report, and reading it is the review that the commit stands for. `--quiet`
# is only the test, and it is asked separately from the answer.
if ! git diff --quiet HEAD -- site; then
    git diff --stat HEAD -- site >&2
    git diff HEAD -- site >&2
    fail "the documents have changed since site/ was committed; \
read the diff above, and commit the rebuilt files now in the working tree"
fi

echo "site/ is what a fresh build writes"
