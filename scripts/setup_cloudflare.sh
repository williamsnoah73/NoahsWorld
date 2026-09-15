#!/usr/bin/env bash
# One-time Cloudflare Pages setup.
#
# Reads credentials from .env.cloudflare (git-ignored) or the environment,
# creates the Pages projects, stores the values as GitHub Actions secrets,
# and enables automated deployment. Secret values are never printed.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PUBLIC_PROJECT="noahs-world"
PRIVATE_PROJECT="noahs-world-family"
PRODUCTION_BRANCH="main"

if [ -f .env.cloudflare ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env.cloudflare
  set +a
fi

missing=0
for name in CLOUDFLARE_ACCOUNT_ID CLOUDFLARE_API_TOKEN; do
  if [ -z "${!name:-}" ]; then
    echo "Missing $name." >&2
    missing=1
  fi
done

if [ "$missing" -ne 0 ]; then
  cat >&2 <<'USAGE'

Create .env.cloudflare in the repository root (it is git-ignored):

  CLOUDFLARE_ACCOUNT_ID=your-account-id
  CLOUDFLARE_API_TOKEN=your-pages-edit-token

Then re-run: ./scripts/setup_cloudflare.sh
USAGE
  exit 1
fi

export CLOUDFLARE_ACCOUNT_ID CLOUDFLARE_API_TOKEN

wrangler() { npx --yes wrangler@4 "$@"; }

echo "==> Verifying API token"
if ! wrangler pages project list >/tmp/noahsworld-pages-projects.txt 2>/tmp/noahsworld-pages-error.txt; then
  echo "Could not list Pages projects. The token likely lacks Account > Cloudflare Pages > Edit." >&2
  sed -e "s/${CLOUDFLARE_API_TOKEN}/***/g" /tmp/noahsworld-pages-error.txt >&2 || true
  rm -f /tmp/noahsworld-pages-error.txt /tmp/noahsworld-pages-projects.txt
  exit 1
fi

for project in "$PUBLIC_PROJECT" "$PRIVATE_PROJECT"; do
  if grep -q "\b${project}\b" /tmp/noahsworld-pages-projects.txt; then
    echo "==> Pages project '${project}' already exists"
  else
    echo "==> Creating Pages project '${project}'"
    wrangler pages project create "$project" --production-branch "$PRODUCTION_BRANCH"
  fi
done
rm -f /tmp/noahsworld-pages-projects.txt /tmp/noahsworld-pages-error.txt

echo "==> Storing GitHub Actions secrets"
printf '%s' "$CLOUDFLARE_ACCOUNT_ID" | gh secret set CLOUDFLARE_ACCOUNT_ID
printf '%s' "$CLOUDFLARE_API_TOKEN" | gh secret set CLOUDFLARE_API_TOKEN

echo "==> Enabling automated deployment"
gh variable set CLOUDFLARE_DEPLOY_ENABLED --body true

cat <<'DONE'

Setup complete. Next:

  1. Delete .env.cloudflare once you are happy with the setup.
  2. Push or re-run the "Validate and deploy public site" workflow to publish a preview.

DONE
