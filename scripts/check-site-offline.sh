#!/usr/bin/env bash
#
# Rebuild the site from the documents already fetched
# and refuse the commit if it differs from what is staged.
#
# A change to the code changes what a build writes,
# so a commit that leaves `site/` as the old code wrote it
# publishes pages no commit of the code would produce.
# `--offline` fetches nothing, so this is quick, needs no credentials,
# and sees only what the code did, not what the documents now say:
# that is the push check's job (`scripts/check-committed-site.sh`).
#
# `pre-commit` stashes unstaged changes before running hooks,
# so the working tree here is what is being committed.

set -euo pipefail

uv run eta-publish all --offline >/dev/null

# Against the index, not `HEAD`: staged changes are the commit, not a difference.
# New files too; what `.gitignore` leaves out (the PDFs, the images) is not listed.
new=$(git ls-files --others --exclude-standard -- site)
if ! git diff --quiet -- site || [[ -n $new ]]; then
    # `--no-pager`: see `scripts/check-committed-site.sh`.
    git --no-pager diff --stat -- site >&2
    git --no-pager diff -- site >&2
    if [[ -n $new ]]; then
        echo "$new" >&2
    fi
    echo "an offline build changes site/; \
read the diff above, and stage the rebuilt files now in the working tree" >&2
    exit 1
fi
