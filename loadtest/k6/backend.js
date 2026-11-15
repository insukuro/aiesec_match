import http from 'k6/http';
import { check, sleep } from 'k6';
import { SharedArray } from 'k6/data';
import { profiles } from './profiles.js';

const BASE = __ENV.BACKEND_URL || 'http://backend:8000';
const TOKENS = new SharedArray('tokens', () => JSON.parse(open('/data/tokens.json')));

export const options = profiles[__ENV.PROFILE || 'baseline'];

const auth = (i) => ({ headers: { Authorization: `Bearer ${TOKENS[i % TOKENS.length].token}` } });
const rand = (n) => Math.floor(Math.random() * n);

export default function () {
  const a = auth(__VU);
  const r = Math.random();

  if (r < 0.25) {
    // GET /me — самый частый, не требует профиля
    const res = http.get(`${BASE}/api/v1/me`, { ...a, tags: { ep: 'me' } });
    check(res, { 'me 200': (x) => x.status === 200 });

  } else if (r < 0.45) {
    // GET /opportunities — каталог, не требует профиля
    const res = http.get(`${BASE}/api/v1/opportunities?limit=20&offset=${rand(200)}`, {
      ...a, tags: { ep: 'opps' },
    });
    check(res, { 'opps 200': (x) => x.status === 200 });

  } else if (r < 0.60) {
    // GET /recommendations/latest — 404 нормален, если run ещё не создан
    const res = http.get(`${BASE}/api/v1/recommendations/latest`, {
      ...a, tags: { ep: 'rec_latest' },
    });
    check(res, { 'rec_latest 200/404': (x) => x.status === 200 || x.status === 404 });

  } else if (r < 0.72) {
    // GET /meta/form-schema — публичный
    const res = http.get(`${BASE}/api/v1/meta/form-schema`, { tags: { ep: 'schema' } });
    check(res, { 'schema 200': (x) => x.status === 200 });

  } else if (r < 0.82) {
    // GET /profiles/me — 404 нормален, если PUT ещё не было в этой итерации
    // (seed создаёт профиль всем, но если seed пуст — увидим 404)
    const res = http.get(`${BASE}/api/v1/profiles/me`, { ...a, tags: { ep: 'profile' } });
    check(res, { 'profile 200/404': (x) => x.status === 200 || x.status === 404 });

  }  else if (r < 0.90) {
    // PUT /profiles/me
    // ← FIX: consent обязателен (profiles.py: ConsentRequired)
    http.post(
      `${BASE}/api/v1/me/consents`,
      JSON.stringify({ kind: 'pd_processing', version: 'v1' }),
      {
        ...a,
        headers: { ...a.headers, 'Content-Type': 'application/json' },
        tags: { ep: 'consent' },
      },
    );

    // ← FIX: полный payload — покрывает missing_for_match (study.status, birth_date,
    //         english_level, programmes) и даёт матчеру данные для scoring.
    const body = JSON.stringify({
      programmes: ['volunteer'],
      english_level: 'B2',
      study: { status: 'bachelor' },
      work_experience: '1_2_years',
      spheres: ['marketing'],
      activities: ['marketing'],
      desired_countries: ['PL'],
      duration: { min_weeks: 6, max_weeks: 12 },
      start_window: '2026-03',
      motivation_text: 'Load test profile',
      birth_date: '2000-01-01',
    });
    const res = http.put(`${BASE}/api/v1/profiles/me`, body, {
      ...a,
      headers: { ...a.headers, 'Content-Type': 'application/json' },
      tags: { ep: 'profile_put' },
    });
    check(res, { 'profile_put 2xx': (x) => x.status < 300 });

  } else if (r < 0.96) {
    // POST /recommendations
    // ← FIX 3: Idempotency-Key ОБЯЗАТЕЛЕН (recommendations.py: Header(min_length=8))
    // ← FIX 4: уникальный на итерацию, иначе вернётся закешированный run
    const body = JSON.stringify({ limit_per_programme: 10, mode: 'sync' });
    const res = http.post(`${BASE}/api/v1/recommendations`, body, {
      ...a,
      headers: {
        ...a.headers,
        'Content-Type': 'application/json',
        'Idempotency-Key': `k6-${__VU}-${__ITER}-${Date.now()}`,
      },
      tags: { ep: 'rec_create' },
    });
    check(res, { 'rec_create 2xx': (x) => x.status < 300 });

  } else {
    // POST /feedback — 409 нормален (уникальный индекс user_id+opportunity_id)
    const body = JSON.stringify({ opportunity_id: 1 + rand(5000), signal: 'opened' });
    const res = http.post(`${BASE}/api/v1/feedback`, body, {
      ...a,
      headers: { ...a.headers, 'Content-Type': 'application/json' },
      tags: { ep: 'feedback' },
    });
    check(res, { 'feedback 2xx/409': (x) => x.status < 300 || x.status === 409 });
  }

  sleep(1 + Math.random() * 3);
}