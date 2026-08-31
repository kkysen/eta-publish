#!/usr/bin/env bash
#
# Fail a push that would fail the deploy.
#
# A push to `main` republishes the site by fetching the documents, and the
# workflow then refuses to deploy unless what it built matches the committed
# `site/`. That check is the whole reason the built site is in the
# repository: it is how a deploy is reviewed before it happens. Finding out
# from a red workflow ten minutes later is the same check, later and further
# away, so this runs it here.
#
# It builds into `site/` rather than somewhere else, for two reasons: the
# images are cached there, so a rebuild that changes nothing downloads
# nothing, and if the check does fail, the tree is left holding exactly the
# files to read and commit.
#
# `git push --no-verify` skips it, which is the right move when the network
# or the credentials are the thing that is missing rather than the build.

set -euo pipefail

# `pre-commit` sets this on a pre-push hook. Only `main` deploys, so only a
# push to `main` can fail the deploy. Unset means this was run by hand.
remote_branch="${PRE_COMMIT_REMOTE_BRANCH:-}"
if [[ -n $remote_branch && ${remote_branch##*/} != main ]]; then
    echo "not pushing to main; the published build is not checked"
    exit 0
fi

if ! git diff --quiet -- site || ! git diff --cached --quiet -- site; then
    echo "site/ has uncommitted changes, and the check rebuilds into it." >&2
    echo "Commit or stash them first." >&2
    exit 1
fi

echo "rebuilding site/ from the documents, the way the deploy will..."
if ! uv run eta-publish -o site; then
    echo >&2
    echo "the build failed, so the deploy would too." >&2
    echo "If the network or the credentials are what is missing rather than" >&2
    echo "the build, push with --no-verify." >&2
    exit 1
fi

if ! git diff --quiet -- site; then
    git diff --stat -- site >&2
    echo >&2
    echo "the documents have changed since site/ was committed, so the" >&2
    echo "deploy would publish something that was never reviewed." >&2
    echo "The rebuilt files are in the working tree: read the diff and" >&2
    echo "commit it, which is the same act as reviewing it." >&2
    exit 1
fi

echo "site/ is what a fresh build writes"
