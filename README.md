# Noah's World

A modern, responsive rebuild of Noah's original Apple iWeb journal and photo site.

## Stack

- Astro static output
- TypeScript
- Astro image optimization (AVIF, WebP, and fallback images)
- Cloudflare Pages for hosting and HTTPS
- Cloudflare Access for the separate private family site
- GitHub Actions for validation and deployment

The legacy iWeb export remains in `Welcome_to_Noahs_World/` as source material. It is not copied into either deployed site.

## Local development

Requirements: Node.js 22.12 or newer, npm, Python 3, and Git LFS.

```sh
git lfs pull
npm ci
npm run dev
```

Build and validate the public site:

```sh
npm test
```

Build the private family site separately:

```sh
npm run build:private
```

The generated directories are `dist/` and `dist-private/`.

## Content migration

The repeatable migration script reads the iWeb HTML/RSS sources, copies only full-size gallery originals, and writes normalized content entries and `reports/migration-manifest.json`.

```sh
python3 scripts/migrate_legacy.py
npm run validate:content
```

Public and private source media are physically separated. Never import `private-site/assets` from the public Astro project.

## Cloudflare setup

Expected hosting cost is $0/month under Cloudflare's current Free limits for this site's size and update frequency. Verify current limits before launch.

1. Add `noahwilliams.me` to Cloudflare DNS or delegate the zone to Cloudflare.
2. In the Cloudflare dashboard, create an API token with **Account → Cloudflare Pages → Edit** and copy your **Account ID** from the account home page.
3. Create `.env.cloudflare` in the repository root. The file is git-ignored, so the values never enter version control:

   ```
   CLOUDFLARE_ACCOUNT_ID=your-account-id
   CLOUDFLARE_API_TOKEN=your-pages-edit-token
   ```

4. Run `./scripts/setup_cloudflare.sh`. It verifies the token, creates the `noahs-world` and `noahs-world-family` Direct Upload projects if missing, stores both values as GitHub Actions secrets, and sets the repository variable `CLOUDFLARE_DEPLOY_ENABLED=true`. Secret values are never printed. Delete `.env.cloudflare` afterwards.

   Until `CLOUDFLARE_DEPLOY_ENABLED` is `true`, pushes validate and build but intentionally skip deployment.

5. Push `modernization` to create a branch preview; merges to `main` deploy production.
6. Attach `noahwilliams.me` to `noahs-world` only after preview approval.
7. Attach `family.noahwilliams.me` to `noahs-world-family`.
8. Create a Cloudflare Access self-hosted application covering `family.noahwilliams.me/*`. Add only approved family email addresses and enable one-time PIN or an identity provider.
9. Verify unauthenticated requests to both private HTML pages and direct image URLs are denied.
10. Optionally redirect `www.noahwilliams.me` to the apex. Do not change `noahwilliams.com` or `noahwilliams.net`.

The public workflow validates pull requests and pushes to `main` or `modernization`; deployment remains gated by `CLOUDFLARE_DEPLOY_ENABLED`. The private workflow uses a protected GitHub environment named `private-family-site`; configure required reviewers if desired.

## DNS cutover

Before changing DNS, export the current records. The existing `noahwilliams.me` endpoint currently presents a mismatched TLS certificate, so verify the new Pages certificate is active before enabling HSTS. Keep GitHub Pages available until the Cloudflare deployment has passed external smoke tests.

## Publishing

Stories and albums live in structured JSON content entries. For an occasional update:

1. Add the original images to the appropriate public or private asset directory.
2. Add or edit the matching content entry.
3. Run `npm test` (and `npm run build:private` for private changes).
4. Open a pull request and review the generated preview/build.
5. Merge to `main`; GitHub Actions deploys automatically.

## Rollback

Cloudflare Pages retains deployments. Promote the last known-good deployment in the Cloudflare dashboard, or revert the problematic Git commit and let GitHub Actions redeploy. DNS can also be restored from the pre-cutover export if needed.
