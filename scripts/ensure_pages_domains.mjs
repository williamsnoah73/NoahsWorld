#!/usr/bin/env node

const API_BASE = 'https://api.cloudflare.com/client/v4';
const ACCEPTED_STATUSES = new Set(['active', 'pending']);

function describeErrors(payload) {
  const errors = Array.isArray(payload?.errors) ? payload.errors : [];
  if (errors.length === 0) {
    return 'Cloudflare returned an unspecified API error';
  }

  return errors
    .map((error) => {
      const code = error?.code === undefined ? 'unknown' : error.code;
      const message = error?.message || 'No error message';
      return `[${code}] ${message}`;
    })
    .join('; ');
}

export function createCloudflareClient({ accountId, apiToken, fetchImpl = fetch }) {
  const projectPath = `${API_BASE}/accounts/${encodeURIComponent(accountId)}/pages/projects/noahs-world/domains`;

  async function request(method, url, body) {
    let response;
    try {
      response = await fetchImpl(url, {
        method,
        headers: {
          Authorization: `Bearer ${apiToken}`,
          'Content-Type': 'application/json',
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    } catch (error) {
      throw new Error(`Cloudflare API request failed: ${error.message}`);
    }

    const text = await response.text();
    let payload;
    try {
      payload = text ? JSON.parse(text) : {};
    } catch {
      throw new Error(`Cloudflare API returned invalid JSON (HTTP ${response.status})`);
    }

    if (!response.ok || payload.success !== true) {
      throw new Error(`Cloudflare API error (HTTP ${response.status}): ${describeErrors(payload)}`);
    }

    return payload.result;
  }

  return {
    async listDomains() {
      const result = await request('GET', `${projectPath}?per_page=100`);
      if (!Array.isArray(result)) {
        throw new Error('Cloudflare API returned an invalid custom-domain list');
      }
      return result;
    },

    createDomain(name) {
      return request('POST', projectPath, { name });
    },
  };
}

function assertAcceptedDomain(domain, expectedName) {
  if (domain?.name !== expectedName) {
    throw new Error(`Cloudflare returned an unexpected custom domain for ${expectedName}`);
  }
  if (!ACCEPTED_STATUSES.has(domain.status)) {
    throw new Error(
      `Custom domain ${expectedName} has unexpected status "${domain.status ?? 'unknown'}"`,
    );
  }
}

export async function ensurePagesDomains(client, domainNames, log = console.log) {
  let domains = await client.listDomains();

  for (const name of domainNames) {
    const existing = domains.find((domain) => domain?.name === name);
    if (existing) {
      assertAcceptedDomain(existing, name);
      log(`Custom domain ${name} already exists with status ${existing.status}.`);
      continue;
    }

    try {
      const created = await client.createDomain(name);
      assertAcceptedDomain(created, name);
      domains = [...domains, created];
      log(`Attached custom domain ${name} with status ${created.status}.`);
    } catch (createError) {
      domains = await client.listDomains();
      const concurrent = domains.find((domain) => domain?.name === name);
      if (!concurrent) {
        throw createError;
      }

      assertAcceptedDomain(concurrent, name);
      log(`Custom domain ${name} already exists with status ${concurrent.status}.`);
    }
  }
}

async function main() {
  const accountId = process.env.CLOUDFLARE_ACCOUNT_ID;
  const apiToken = process.env.CLOUDFLARE_API_TOKEN;
  const missing = [
    !accountId && 'CLOUDFLARE_ACCOUNT_ID',
    !apiToken && 'CLOUDFLARE_API_TOKEN',
  ].filter(Boolean);

  if (missing.length > 0) {
    throw new Error(`Missing required environment variable(s): ${missing.join(', ')}`);
  }

  const client = createCloudflareClient({ accountId, apiToken });
  await ensurePagesDomains(client, ['noahwilliams.me', 'www.noahwilliams.me']);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
