import http from 'k6/http';
import { check, fail } from 'k6';

const BASE = __ENV.BACKEND_URL || 'http://backend:8000';

export const options = {
  scenarios: {
    e2e: {
      executor: 'constant-vus',
      vus: Number(__ENV.E2E_VUS || 10),
      duration: __ENV.E2E_DURATION || '5m',
    },
  },
  thresholds: {
    checks: ['rate>0.98'],
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.02'],
  },
};

const J = (obj) => ({ headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(obj) });

function uniqEmail() {
  // ← FIX: домен с валидным TLD — Pydantic EmailStr отвергает .local
  return `e2e+${__VU}-${__ITER}-${Date.now()}@loadtest.example.com`;
}

export default function () {
  const email = uniqEmail();
  const pass = 'TestPass123';

  // ---- 1. register ----
  const reg = http.post(
    `${BASE}/api/v1/auth/register`,
    JSON.stringify({ email, password: pass }),
    J(),
  );
  if (!check(reg, { 'register 2xx': (r) => r.status < 300 })) return;
  const token = reg.json('access_token');
  if (!token) { fail('register: no access_token'); return; }

  const H = { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } };

  // ---- 2. consent (ОБЯЗАТЕЛЬНО перед PUT /profiles/me) ----
  const consent = http.post(
    `${BASE}/api/v1/me/consents`,
    JSON.stringify({ kind: 'pd_processing', version: 'v1' }),
    H,
  );
  check(consent, { 'consent 2xx': (r) => r.status < 300 });

  // ---- 3. PUT profile (с birth_date!) ----
  const profileBody = {
    programmes: ['volunteer'],
    english_level: 'B2',
    study: { status: 'bachelor' },
    work_experience: '1_2_years',
    spheres: ['marketing'],
    activities: ['marketing'],
    desired_countries: ['PL'],
    duration: { min_weeks: 6, max_weeks: 12 },
    start_window: '2026-03',
    motivation_text: 'E2E test profile',
    birth_date: '2000-01-01',
  };
  const put = http.put(`${BASE}/api/v1/profiles/me`, JSON.stringify(profileBody), H);
  check(put, { 'profile_put 2xx': (r) => r.status < 300 });

  // Проверка консистентности: study.status должен сохраниться
  const got = http.get(`${BASE}/api/v1/profiles/me`, H);
  check(got, {
    'profile_get 200': (r) => r.status === 200,
    'profile study.status persisted': (r) => {
      try { return r.json('study').status === 'bachelor'; } catch { return false; }
    },
    'profile completeness == 1.0': (r) => {
      try { return r.json('completeness') === 1; } catch { return false; }
    },
  });

  // ---- 5. POST recommendations (sync) с Idempotency-Key ----
  const recHeaders = {
    ...H.headers,
    'Idempotency-Key': `e2e-${__VU}-${__ITER}-${Date.now()}`,
  };
  const rec = http.post(
    `${BASE}/api/v1/recommendations`,
    JSON.stringify({ limit_per_programme: 10, mode: 'sync' }),
    { headers: recHeaders },
  );
  check(rec, { 'rec_create 2xx': (r) => r.status < 300 });
  const runId = rec.json('run_id');
  const recState = rec.json('state');

  check(rec, {
    'rec_create returns run_id': () => !!runId,
    'rec_create state succeeded': () => recState === 'succeeded',
  });
  if (!runId) return;

  // ---- 6. GET recommendations/{run_id} — тот же run ----
  const byId = http.get(`${BASE}/api/v1/recommendations/${runId}`, H);
  check(byId, {
    'rec_get 200': (r) => r.status === 200,
    'rec_get same run_id': (r) => {
      try { return r.json('run_id') === runId; } catch { return false; }
    },
    'rec_get groups is array': (r) => {
      try { return Array.isArray(r.json('groups')); } catch { return false; }
    },
  });

  // ---- 7. GET latest — тот же run_id ----
  const latest = http.get(`${BASE}/api/v1/recommendations/latest`, H);
  check(latest, {
    'rec_latest 200': (r) => r.status === 200,
    'rec_latest == created run_id': (r) => {
      try { return r.json('run_id') === runId; } catch { return false; }
    },
  });

  // ---- 8. POST feedback (liked) ----
  const oppId = (() => {
    try {
      const groups = byId.json('groups') || [];
      for (const g of groups) {
        if (g.items && g.items.length) return g.items[0].opportunity.opportunity_id;
      }
    } catch { /* ignore */ }
    return 1;
  })();

  const fb = http.post(
    `${BASE}/api/v1/feedback`,
    JSON.stringify({ opportunity_id: oppId, signal: 'liked', run_id: runId }),
    H,
  );
  check(fb, { 'feedback 2xx': (r) => r.status < 300 });

  // ---- 9. GET liked — содержит oppId ----
  const liked = http.get(`${BASE}/api/v1/feedback/liked`, H);
  check(liked, {
    'liked 200': (r) => r.status === 200,
    'liked contains opportunity': (r) => {
      try {
        const body = r.json();
        const items = body.items ?? body.data ?? body;
        const arr = Array.isArray(items) ? items : [];
        return arr.some((x) => (x.opportunity_id ?? x.opportunity?.opportunity_id) === oppId);
      } catch { return false; }
    },
  });

  // ---- 10. DELETE /me — идемпотентность прогонов ----
  const del = http.del(`${BASE}/api/v1/me`, null, H);
  check(del, { 'me_delete 2xx/204': (r) => r.status < 300 });
}