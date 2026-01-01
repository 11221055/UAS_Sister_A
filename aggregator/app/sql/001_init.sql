CREATE TABLE IF NOT EXISTS processed_events (
  topic TEXT NOT NULL,
  event_id TEXT NOT NULL,
  first_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
  source TEXT NOT NULL,
  PRIMARY KEY (topic, event_id)
);

CREATE TABLE IF NOT EXISTS events (
  topic TEXT NOT NULL,
  event_id TEXT NOT NULL,
  ts TIMESTAMPTZ NOT NULL,
  source TEXT NOT NULL,
  payload JSONB NOT NULL,
  inserted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (topic, event_id),
  FOREIGN KEY (topic, event_id) REFERENCES processed_events(topic, event_id)
);

CREATE TABLE IF NOT EXISTS stats (
  id BIGINT PRIMARY KEY DEFAULT 1,
  received BIGINT NOT NULL DEFAULT 0,
  unique_processed BIGINT NOT NULL DEFAULT 0,
  duplicate_dropped BIGINT NOT NULL DEFAULT 0,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO stats(id) VALUES (1) ON CONFLICT DO NOTHING;
