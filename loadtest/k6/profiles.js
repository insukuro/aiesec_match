export const profiles = {
  baseline: {
    scenarios: {
      main: { executor: 'constant-vus', vus: 20, duration: '10m' },
    },
    thresholds: {
      http_req_duration: ['p(95)<500', 'p(99)<1000'],
      http_req_failed: ['rate<0.01'],
    },
  },

  stress: {
    scenarios: {
      main: {
        executor: 'ramping-vus',
        startVUs: 0,
        stages: [
          { duration: '1m', target: 20 },
          { duration: '2m', target: 20 },
          { duration: '2m', target: 100 },
          { duration: '2m', target: 100 },
          { duration: '2m', target: 300 },
          { duration: '2m', target: 300 },
          { duration: '2m', target: 500 },
          { duration: '1m', target: 0 },
        ],
      },
    },
    thresholds: {
      http_req_duration: ['p(95)<1000', 'p(99)<3000'],
      http_req_failed: ['rate<0.05'],
    },
  },

  spike: {
    scenarios: {
      main: {
        executor: 'ramping-vus',
        stages: [
          { duration: '10s', target: 300 },
          { duration: '1m',  target: 300 },
          { duration: '20s', target: 0 },
        ],
      },
    },
  },
};

// ВАЖНО: spheres/other_languages/nationality — строки, как в taxonomy.yaml.
// Валидные значения (из присланного маппинга):
//   spheres:       marketing, sales, teaching_*
//   languages:     en, ru, es, pt
//   nationalities: RU, AZ
const SAMPLES = [
  { programmes: ['teacher'],  english_level: 'B2', spheres: ['teaching_arts'],      activities: [], desired_countries: ['RO'], other_languages: ['en', 'ru'], nationality: 'RU', duration: { min_weeks: 6,  max_weeks: 12 } },
  { programmes: ['teacher'],  english_level: 'C1', spheres: ['teaching_languages'], activities: [], desired_countries: ['PL'], other_languages: ['en', 'es'], nationality: 'AZ', duration: { min_weeks: 8,  max_weeks: 16 } },
  { programmes: ['teacher'],  english_level: 'B1', spheres: ['teaching_math'],      activities: [], desired_countries: ['TR'], other_languages: ['en'],       nationality: 'RU', duration: { min_weeks: 4,  max_weeks: 8  } },
  { programmes: ['talent'],   english_level: 'B2', spheres: ['marketing'],         activities: [], desired_countries: ['DE'], other_languages: ['en', 'pt'], nationality: 'RU', duration: { min_weeks: 12, max_weeks: 24 } },
  { programmes: ['talent'],   english_level: 'C1', spheres: ['sales'],             activities: [], desired_countries: ['FR'], other_languages: ['en', 'es'], nationality: 'AZ', duration: { min_weeks: 12, max_weeks: 24 } },
  { programmes: ['talent'],   english_level: 'B1', spheres: ['marketing', 'sales'], activities: [], desired_countries: ['NL'], other_languages: ['en'],       nationality: 'RU', duration: { min_weeks: 10, max_weeks: 20 } },
  { programmes: ['volunteer'], english_level: 'B2', spheres: ['marketing'],        activities: ['marketing'], desired_countries: ['PL'], other_languages: ['en', 'ru'], nationality: 'RU', duration: { min_weeks: 6, max_weeks: 12 } },
  { programmes: ['volunteer'], english_level: 'A2', spheres: ['sales'],            activities: ['sales'],     desired_countries: ['TR'], other_languages: ['en'],       nationality: 'AZ', duration: { min_weeks: 4, max_weeks: 8  } },
  { programmes: ['volunteer'], english_level: 'C2', spheres: ['teaching_arts'],    activities: [],            desired_countries: ['IT'], other_languages: ['en', 'es'], nationality: 'RU', duration: { min_weeks: 6, max_weeks: 12 } },
  { programmes: ['talent', 'teacher'], english_level: 'B2', spheres: ['marketing', 'teaching_arts'], activities: [], desired_countries: ['DE'], other_languages: ['en'], nationality: 'RU' },
  { programmes: ['volunteer', 'talent'], english_level: 'B1', spheres: ['sales', 'marketing'], activities: ['marketing'], desired_countries: ['ES'], other_languages: ['en', 'pt'], nationality: 'AZ' },
  { programmes: ['volunteer', 'teacher'], english_level: 'C1', spheres: ['teaching_languages'], activities: [], desired_countries: ['PL'], other_languages: ['en', 'ru'], nationality: 'RU' },
  { programmes: ['teacher'],  english_level: 'B2', spheres: ['teaching_science'], activities: [], desired_countries: ['RO'], other_languages: ['en'], nationality: 'RU', study: { level: 'bachelor' } },
  { programmes: ['talent'],   english_level: 'C1', spheres: ['marketing'],        activities: [], desired_countries: ['DE'], other_languages: ['en', 'es'], nationality: 'AZ', study: { level: 'school' } },
];

export function pickProfile() {
  return SAMPLES[Math.floor(Math.random() * SAMPLES.length)];
}