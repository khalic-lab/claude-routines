-- Phase-2 analytical plane (ARCHITECTURE.md §3/§5.2, built 2026-07-18): local Postgres +
-- pgvector, loaded from the repo's story ledger by tools/plane/sync.py. One database answers
-- both query families: vector search ("what's near this") and relational/graph queries
-- (threads, entities, sources, feedback) — the calibration lesson (2026-05-31) is that cosine
-- gives NEARNESS, never relationship TYPE; the typed edges live in ordinary columns/joins.
--
-- Idempotent: sync.py applies this file on every run (IF NOT EXISTS throughout).

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS stories (
  sid             text PRIMARY KEY,          -- durable st-{sha1(norm_url)[:12]} store id
  legacy_ids      text[] NOT NULL DEFAULT '{}',
  date            date NOT NULL,             -- first compose date
  stream          text NOT NULL,             -- originating stream
  streams         text[] NOT NULL DEFAULT '{}',
  editions        text[] NOT NULL DEFAULT '{}',
  headline        text NOT NULL,
  summary         text,
  url             text,
  source_domain   text,
  tier            text,
  tags            text[] NOT NULL DEFAULT '{}',
  topics          text[] NOT NULL DEFAULT '{}',
  importance      int,
  entities        text[] NOT NULL DEFAULT '{}',   -- writer-supplied actors/places/artifacts (2026-07-18)
  affiliations    text[] NOT NULL DEFAULT '{}',
  display_body    text,
  why             text,
  thread_id       text,
  first_seen_date date,
  event_date      text,                      -- reduced precision YYYY[-MM[-DD]]
  status          text,                      -- settled | merged-into:<sid> | ...
  embedding_model text,
  embedding       vector(1024)
);
CREATE INDEX IF NOT EXISTS stories_embedding_idx ON stories USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS stories_date_idx      ON stories (date);
CREATE INDEX IF NOT EXISTS stories_thread_idx    ON stories (thread_id);
CREATE INDEX IF NOT EXISTS stories_domain_idx    ON stories (source_domain);

CREATE TABLE IF NOT EXISTS publishes (
  sid     text NOT NULL,
  edition text NOT NULL,                     -- "YYYY-MM-DD-slug"
  ts      timestamptz,
  stream  text,
  PRIMARY KEY (sid, edition)
);

CREATE TABLE IF NOT EXISTS feedback (
  fb_id   text PRIMARY KEY,
  sid     text,
  brief   text,
  vote    int,
  reason  text,
  reader  text,
  surface text,
  ts      timestamptz
);

-- threads: one row per developing story line (the graph's strongest edge type)
CREATE OR REPLACE VIEW threads AS
SELECT thread_id,
       count(*)                    AS stories,
       min(date)                   AS first_date,
       max(date)                   AS last_date,
       array_agg(DISTINCT stream)  AS streams,
       (array_agg(headline ORDER BY date))[1] AS genesis_headline
FROM stories
WHERE thread_id IS NOT NULL
GROUP BY thread_id;

-- entity_stories: the entity graph unrolled (populates as writers emit `entities`)
CREATE OR REPLACE VIEW entity_stories AS
SELECT unnest(entities) AS entity, sid, date, stream, headline, importance
FROM stories
WHERE entities <> '{}';
