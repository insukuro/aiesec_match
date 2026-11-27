import { check, sleep } from 'k6';
import exec from 'k6/execution';
import http from 'k6/http';
import { Counter, Trend } from 'k6/metrics';

const BASE = __ENV.BACKEND_URL || 'http://backend:8000';
const RUN = __ENV.RUN_ID;
const MODE = __ENV.TEST_CASE || 'NT01';
const USERS = Number(__ENV.USERS || (MODE === 'NT03' ? 15 : 10));
const HOLD = Number(__ENV.HOLD_SECONDS || (MODE === 'NT03' ? 180 : 600));
const SIZE = Number(__ENV.CATALOG_SIZE || 1000);
const CONTROL = MODE === 'NT01';
if (!/^[a-z0-9-]{8,48}$/.test(RUN || '') || !['NT01', 'NT02', 'NT03'].includes(MODE)
    || (MODE === 'NT02' && USERS !== 10)
    || (MODE === 'NT03' && ![15, 20].includes(USERS))
    || !Number.isInteger(HOLD) || HOLD < 60
    || !Number.isInteger(SIZE) || SIZE < 1 || SIZE > 1000000) {
  throw new Error('Check RUN_ID, TEST_CASE, USERS, HOLD_SECONDS and CATALOG_SIZE');
}

const operations = new Counter('match_started');
const outcomes = new Counter('match_completed');
const successes = new Counter('match_success');
const iterationWall = new Trend('candidate_iteration', true);
const wall = new Trend('match_wall', true);
const seen = new Set();

export const options = {
  tags: { run_id: RUN, test_case: MODE },
  setupTimeout: '2m',
  maxRedirects: 0,
  scenarios: {
    candidate: CONTROL
      ? { executor: 'per-vu-iterations', vus: 1, iterations: 1, maxDuration: '1m' }
      : {
        executor: 'ramping-vus', startVUs: 0, gracefulRampDown: '15s', gracefulStop: '15s',
        stages: [
          { duration: '60s', target: USERS },
          { duration: HOLD + 's', target: USERS },
          { duration: '30s', target: 0 },
        ],
      },
  },
};

function request(token, phase, key = '') {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = 'Bearer ' + token;
  if (key) headers['Idempotency-Key'] = key;
  return { headers, tags: { phase }, timeout: '15s' };
}

function requireStatus(response, expected, step) {
  if (response.status !== expected) throw new Error(step + ': HTTP ' + response.status);
  return response;
}

function match(token, phase, key) {
  const params = request(token, phase, key);
  params.tags.op = 'recommend';
  params.responseCallback = http.expectedStatuses(200);
  return http.post(BASE + '/api/v1/recommendations',
    '{"mode":"sync","limit_per_programme":10}', params);
}

function parseValid(response, version) {
  if (response.status !== 200) return null;
  try {
    const body = response.json();
    if (!body.run_id || body.state !== 'succeeded' || body.profile_version !== version
        || !Array.isArray(body.groups) || body.groups.length !== 1) return null;
    const group = body.groups[0];
    if (group.programme_kind !== 'talent' || !Array.isArray(group.items)
        || group.items.length < 1 || group.items.length > 10) return null;
    const ids = new Set();
    for (const item of group.items) {
      const card = item.opportunity;
      const id = card.opportunity_id;
      if (!Number.isInteger(id) || id < 8000000 || id >= 8000000 + SIZE || ids.has(id)
          || card.is_open !== true || card.programme.kind !== 'talent'
          || card.capacity.available_openings < 1
          || !Number.isFinite(item.score) || item.score < 0 || item.score > 1
          || !['excellent', 'good', 'fair'].includes(item.label)
          || !Array.isArray(item.reasons)) return null;
      ids.add(id);
    }
    return body;
  } catch (_) {
    return null;
  }
}

export function setup() {
  const phase = 'setup';
  const meta = requireStatus(http.get(BASE + '/api/v1/meta/consents', request(null, phase)), 200, 'consents');
  const consent = meta.json('consents').find((doc) => doc.kind === 'pd_processing');
  if (!consent || !consent.version) throw new Error('Missing pd_processing version');
  const accounts = [];
  const profile = {
    programmes: ['talent'], english_level: 'B2', study: { status: 'bachelor' },
    spheres: ['marketing', 'sales'], nationality: 'RU',
    other_languages: ['ru', 'es', 'pt'], birth_date: '2000-01-01',
  };
  for (let i = 1; i <= (CONTROL ? 1 : USERS); i++) {
    const email = 'nt+' + RUN + '-' + i + '@loadtest.example.com';
    const auth = requireStatus(http.post(BASE + '/api/v1/auth/register',
      JSON.stringify({ email, password: 'TestPass123' }), request(null, phase)), 200, 'register');
    const token = auth.json('access_token');
    if (!token) throw new Error('Missing access token');
    const params = request(token, phase);
    requireStatus(http.post(BASE + '/api/v1/me/consents',
      JSON.stringify({ kind: consent.kind, version: consent.version }), params), 204, 'consent');
    const saved = requireStatus(http.put(BASE + '/api/v1/profiles/me',
      JSON.stringify(profile), params), 200, 'profile');
    const version = saved.json('profile_version');
    if (!Number.isInteger(version)) throw new Error('Invalid profile version');
    accounts.push({ token, version });
  }

  const { token, version } = accounts[0];
  const key = RUN + '-probe';
  const first = parseValid(match(token, phase, key), version);
  const replay = parseValid(match(token, phase, key), version);
  const next = parseValid(match(token, phase, RUN + '-probe-new'), version);
  if (!first || !replay || !next || replay.run_id !== first.run_id || next.run_id === first.run_id) {
    throw new Error('Preflight failed: invalid recommendations or idempotency');
  }
  console.info('preflight OK; run ids: ' + first.run_id + ', ' + replay.run_id + ', ' + next.run_id);
  return { accounts, previousIds: [first.run_id, next.run_id] };
}

export default function ({ accounts, previousIds }) {
  const vu = exec.vu.idInTest;
  const iteration = exec.vu.iterationInScenario;
  const { token, version } = accounts[vu - 1];
  const iterationStart = Date.now();
  const elapsed = iterationStart - exec.scenario.startTime;
  const phase = CONTROL ? 'control' : elapsed < 60000 ? 'ramp'
    : elapsed < (60 + HOLD) * 1000 ? 'plateau' : 'down';
  if (iteration === 0) console.info('scenario_start_ms=' + exec.scenario.startTime);
  const tags = { phase };
  const key = RUN + '-vu' + vu + '-op' + iteration;
  operations.add(1, tags);
  const start = Date.now();
  const response = match(token, phase, key);
  const milliseconds = Date.now() - start;
  const body = parseValid(response, version);
  const valid = Boolean(body && !seen.has(body.run_id) && !previousIds.includes(body.run_id));
  if (valid) seen.add(body.run_id);
  check(valid, { 'new completed run with valid cards': (ok) => ok }, tags);
  outcomes.add(1, tags);
  successes.add(Number(valid), tags);
  if (valid) wall.add(milliseconds, tags);
  if (!valid) console.warn('match failed: VU=' + vu + ' iteration=' + iteration + ' HTTP=' + response.status);
  if (!CONTROL) sleep(2 + ((vu + iteration) % 3));
  iterationWall.add(Date.now() - iterationStart, tags);
}
