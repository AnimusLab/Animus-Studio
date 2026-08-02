-- ============================================================
--  Animus Studio — PostgreSQL Schema
--  Enable pgvector for embeddings
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ─── Users ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email       TEXT UNIQUE NOT NULL,
    username    TEXT UNIQUE NOT NULL,
    full_name   TEXT,
    hashed_password TEXT NOT NULL,
    is_active   BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Brands ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS brands (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    description TEXT,
    tone        TEXT DEFAULT 'professional',
    avoid       TEXT[],
    preferred   TEXT[],
    target_audience TEXT,
    logo_url    TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Channels ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS channels (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id    UUID REFERENCES brands(id) ON DELETE CASCADE,
    platform    TEXT NOT NULL,  -- youtube | instagram | linkedin | x | threads
    channel_id  TEXT,           -- platform-specific identifier
    channel_name TEXT,
    access_token TEXT,
    refresh_token TEXT,
    token_expiry TIMESTAMPTZ,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Voice Profiles ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS voice_profiles (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id    UUID REFERENCES brands(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    tts_provider TEXT DEFAULT 'elevenlabs', -- elevenlabs | cartesia
    tts_voice_id TEXT,
    emotion     TEXT DEFAULT 'neutral',
    pace        FLOAT DEFAULT 1.0,
    pitch       FLOAT DEFAULT 1.0,
    vocabulary  TEXT[],
    fill_words  TEXT[],
    pause_pattern JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Missions ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS missions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id    UUID REFERENCES brands(id) ON DELETE CASCADE,
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    goal        TEXT NOT NULL,
    budget      DECIMAL DEFAULT 0,
    frequency   TEXT,           -- "3 shorts/week", "daily", etc.
    style       TEXT,
    voice_profile_id UUID REFERENCES voice_profiles(id),
    requires_approval BOOLEAN DEFAULT TRUE,
    status      TEXT DEFAULT 'active', -- active | paused | completed | archived
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Jobs (workflow runs) ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS jobs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mission_id  UUID REFERENCES missions(id) ON DELETE CASCADE,
    workflow    TEXT NOT NULL,  -- daily_content | breaking_news | weekly_review
    status      TEXT DEFAULT 'pending', -- pending | running | paused | completed | failed
    current_step TEXT,
    progress    INTEGER DEFAULT 0,
    error       TEXT,
    metadata    JSONB DEFAULT '{}',
    started_at  TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Agent Tasks ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_tasks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id      UUID REFERENCES jobs(id) ON DELETE CASCADE,
    agent_type  TEXT NOT NULL,  -- executive | research | script | review | voice | media | editor | publisher | analytics
    status      TEXT DEFAULT 'pending',
    input       JSONB,
    output      JSONB,
    error       TEXT,
    tokens_used INTEGER DEFAULT 0,
    model_used  TEXT,
    started_at  TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Videos ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS videos (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id      UUID REFERENCES jobs(id),
    brand_id    UUID REFERENCES brands(id) ON DELETE CASCADE,
    title       TEXT,
    description TEXT,
    script      TEXT,
    hook        TEXT,
    cta         TEXT,
    duration_seconds INTEGER,
    file_path   TEXT,
    thumbnail_path TEXT,
    status      TEXT DEFAULT 'draft', -- draft | review | approved | published | failed
    platform_ids JSONB DEFAULT '{}',  -- {youtube: "xxx", instagram: "xxx"}
    published_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Research Items ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS research_items (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id      UUID REFERENCES jobs(id),
    topic       TEXT NOT NULL,
    source      TEXT,           -- reddit | hackernews | youtube | google_trends | arxiv | github
    url         TEXT,
    summary     TEXT,
    audience    TEXT,
    competition TEXT,
    risk_score  FLOAT DEFAULT 0.0,
    raw_data    JSONB DEFAULT '{}',
    embedding   vector(1536),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Analytics ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analytics (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id    UUID REFERENCES videos(id) ON DELETE CASCADE,
    platform    TEXT NOT NULL,
    fetched_at  TIMESTAMPTZ DEFAULT NOW(),
    views       BIGINT DEFAULT 0,
    likes       BIGINT DEFAULT 0,
    comments    BIGINT DEFAULT 0,
    shares      BIGINT DEFAULT 0,
    ctr         FLOAT,
    avg_view_duration FLOAT,
    retention_rate FLOAT,
    subscribers_gained INTEGER DEFAULT 0,
    revenue     DECIMAL DEFAULT 0,
    rpm         DECIMAL DEFAULT 0,
    raw_data    JSONB DEFAULT '{}'
);

-- ─── Knowledge / Memory ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS knowledge (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id    UUID REFERENCES brands(id) ON DELETE CASCADE,
    type        TEXT NOT NULL,  -- creator | brand | audience | video | platform
    title       TEXT,
    content     TEXT NOT NULL,
    embedding   vector(1536),
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Settings ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS settings (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    preferences JSONB DEFAULT '{}',
    llm_config  JSONB DEFAULT '{}',    -- {provider, model, temperature}
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Indexes ──────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_missions_brand ON missions(brand_id);
CREATE INDEX IF NOT EXISTS idx_jobs_mission ON jobs(mission_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_job ON agent_tasks(job_id);
CREATE INDEX IF NOT EXISTS idx_videos_brand ON videos(brand_id);
CREATE INDEX IF NOT EXISTS idx_analytics_video ON analytics(video_id);
CREATE INDEX IF NOT EXISTS idx_research_embedding ON research_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding ON knowledge USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
