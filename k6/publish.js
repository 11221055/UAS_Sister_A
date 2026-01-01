import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 50,
  duration: '20s',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

export default function () {
  const base = __ENV.BASE_URL || 'http://localhost:8080';
  const events = [];
  for (let i = 0; i < 50; i++) {
    const id = Math.random() < 0.3 ? i - 1 : i;
    events.push({
      topic: 'app.auth',
      event_id: `app.auth-${id}`,
      timestamp: new Date().toISOString(),
      source: 'k6',
      payload: { id }
    });
  }

  const res = http.post(`${base}/publish`, JSON.stringify(events), {
    headers: { 'Content-Type': 'application/json' },
  });

  check(res, { 'status ok': (r) => r.status === 200 || r.status === 202 });
  sleep(0.2);
}
