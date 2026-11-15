import http from 'k6/http';
import { check } from 'k6';
import { profiles, pickProfile } from './profiles.js';

const BASE = __ENV.MATCHER_URL || 'http://matcher:8000';

export const options = profiles[__ENV.PROFILE || 'baseline'];

export default function () {
  const payload = JSON.stringify({
    profile: pickProfile(),
    filters: { programme_kinds: [], country_codes: [], exclude_opportunity_ids: [] },
    limit_per_programme: 10,
    explain: true,
  });

  const res = http.post(`${BASE}/v1/match`, payload, {
    headers: { 'Content-Type': 'application/json' },
    tags: { ep: 'match' },
  });

  check(res, {
    'match 200': (r) => r.status === 200,
    'match has groups': (r) => {
      try { return Array.isArray(r.json('groups')); } catch { return false; }
    },
    'match took_ms < 2000': (r) => {
      try { return r.json('took_ms') < 2000; } catch { return false; }
    },
  });
}