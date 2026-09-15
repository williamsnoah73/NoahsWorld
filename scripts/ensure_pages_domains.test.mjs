import assert from 'node:assert/strict';
import test from 'node:test';

import { createCloudflareClient, ensurePagesDomains } from './ensure_pages_domains.mjs';

function response(result, { ok = true, status = 200, errors = [] } = {}) {
  return {
    ok,
    status,
    text: async () => JSON.stringify({ success: ok, result, errors }),
  };
}

test('keeps active and pending domains without creating duplicates', async () => {
  const calls = [];
  const client = createCloudflareClient({
    accountId: 'account',
    apiToken: 'token',
    fetchImpl: async (url, options) => {
      calls.push({ url, options });
      return response([
        { name: 'noahwilliams.me', status: 'active' },
        { name: 'www.noahwilliams.me', status: 'pending' },
      ]);
    },
  });

  await ensurePagesDomains(client, ['noahwilliams.me', 'www.noahwilliams.me'], () => {});

  assert.equal(calls.length, 1);
  assert.equal(calls[0].options.method, 'GET');
});

test('creates each missing domain with the expected API payload', async () => {
  const createdNames = [];
  const client = createCloudflareClient({
    accountId: 'account',
    apiToken: 'token',
    fetchImpl: async (_url, options) => {
      if (options.method === 'GET') {
        return response([]);
      }
      const { name } = JSON.parse(options.body);
      createdNames.push(name);
      return response({ name, status: 'pending' });
    },
  });

  await ensurePagesDomains(client, ['noahwilliams.me', 'www.noahwilliams.me'], () => {});

  assert.deepEqual(createdNames, ['noahwilliams.me', 'www.noahwilliams.me']);
});

test('accepts a domain attached concurrently after a failed create', async () => {
  let listCount = 0;
  const client = createCloudflareClient({
    accountId: 'account',
    apiToken: 'token',
    fetchImpl: async (_url, options) => {
      if (options.method === 'GET') {
        listCount += 1;
        return response(
          listCount === 1 ? [] : [{ name: 'noahwilliams.me', status: 'pending' }],
        );
      }
      return response(null, {
        ok: false,
        status: 409,
        errors: [{ code: 8000006, message: 'Domain already exists' }],
      });
    },
  });

  await ensurePagesDomains(client, ['noahwilliams.me'], () => {});
  assert.equal(listCount, 2);
});

test('surfaces unexpected domain states', async () => {
  const client = {
    listDomains: async () => [{ name: 'noahwilliams.me', status: 'error' }],
    createDomain: async () => {
      throw new Error('should not create');
    },
  };

  await assert.rejects(
    ensurePagesDomains(client, ['noahwilliams.me'], () => {}),
    /unexpected status "error"/,
  );
});

test('surfaces Cloudflare API errors without including the token', async () => {
  const client = createCloudflareClient({
    accountId: 'account',
    apiToken: 'super-secret',
    fetchImpl: async () =>
      response(null, {
        ok: false,
        status: 403,
        errors: [{ code: 10000, message: 'Authentication error' }],
      }),
  });

  await assert.rejects(client.listDomains(), (error) => {
    assert.match(error.message, /HTTP 403.*Authentication error/);
    assert.doesNotMatch(error.message, /super-secret/);
    return true;
  });
});
