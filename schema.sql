-- ============================================================================
-- LandIt Job Matching System - Database Schema
-- ============================================================================

-- Enable vector extension for PostgreSQL (if using pgvector)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Jobs table - stores job postings with embeddings
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT,
    responsibilities TEXT,
    location VARCHAR(255),
    remote_allowed BOOLEAN DEFAULT FALSE,
    salary_min INTEGER,
    salary_max INTEGER,
    currency VARCHAR(10) DEFAULT 'USD',
    experience_level VARCHAR(50), -- 'entry', 'mid', 'senior', 'executive'
    job_type VARCHAR(50), -- 'full-time', 'part-time', 'contract', 'internship'
    industry VARCHAR(100),
    company_size VARCHAR(50), -- 'startup', 'small', 'medium', 'large', 'enterprise'
    benefits TEXT[],
    skills_required TEXT[],
    skills_preferred TEXT[],
    education_required VARCHAR(100),

    -- Vector embeddings (384 dimensions for sentence-transformers all-MiniLM-L6-v2)
    description_embedding VECTOR(384),
    requirements_embedding VECTOR(384),
    title_embedding VECTOR(384),

    -- Metadata
    source VARCHAR(100), -- 'manual', 'api', 'scraper'
    external_job_id VARCHAR(255),
    job_url TEXT,
    application_deadline DATE,
    posted_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for performance
    CONSTRAINT jobs_title_company_unique UNIQUE(title, company, posted_date)
);

-- User resumes table - stores user resume data with embeddings
CREATE TABLE user_resumes (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,

    -- Raw resume data
    resume_text TEXT NOT NULL,
    resume_filename VARCHAR(255),

    -- Structured extracted data from your existing system
    extracted_entities JSONB,
    structured_data JSONB, -- work_experience, education, skills, etc.
    resume_analytics JSONB, -- completeness_score, ats_score, etc.

    -- Vector embeddings
    full_resume_embedding VECTOR(384),
    skills_embedding VECTOR(384),
    experience_embedding VECTOR(384),

    -- User preferences and profile
    desired_job_titles TEXT[],
    preferred_locations TEXT[],
    remote_preference VARCHAR(20) DEFAULT 'flexible', -- 'required', 'preferred', 'no', 'flexible'
    salary_expectation_min INTEGER,
    salary_expectation_max INTEGER,
    willing_to_relocate BOOLEAN DEFAULT FALSE,

    -- Resume metadata
    years_of_experience INTEGER,
    current_job_title VARCHAR(255),
    education_level VARCHAR(100),
    top_skills TEXT[],

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT user_resumes_email_unique UNIQUE(user_email)
);

-- Job recommendations table - stores generated recommendations
CREATE TABLE job_recommendations (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,

    -- Similarity scores (0.0 to 1.0)
    semantic_similarity_score FLOAT NOT NULL,
    skills_match_score FLOAT NOT NULL,
    experience_match_score FLOAT NOT NULL,
    location_match_score FLOAT NOT NULL,
    salary_match_score FLOAT DEFAULT 0.0,

    -- Overall calculated score
    overall_score FLOAT NOT NULL,
    confidence_score FLOAT DEFAULT 0.8,

    -- Explanation data
    match_reasons JSONB, -- detailed explanation of why job was recommended
    skill_matches TEXT[], -- specific skills that matched
    skill_gaps TEXT[], -- skills user is missing

    -- Recommendation metadata
    algorithm_version VARCHAR(50) DEFAULT '1.0',
    recommendation_batch_id UUID,

    -- Status tracking
    is_viewed BOOLEAN DEFAULT FALSE,
    is_saved BOOLEAN DEFAULT FALSE,
    is_applied BOOLEAN DEFAULT FALSE,
    is_dismissed BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    viewed_at TIMESTAMP,

    -- Constraints
    CONSTRAINT job_recommendations_user_job_unique UNIQUE(user_email, job_id),
    CONSTRAINT valid_scores CHECK (
        semantic_similarity_score >= 0 AND semantic_similarity_score <= 1 AND
        skills_match_score >= 0 AND skills_match_score <= 1 AND
        experience_match_score >= 0 AND experience_match_score <= 1 AND
        location_match_score >= 0 AND location_match_score <= 1 AND
        overall_score >= 0 AND overall_score <= 1
    )
);

-- ============================================================================
-- FEEDBACK SYSTEM TABLES
-- ============================================================================

-- User feedback on job recommendations
CREATE TABLE recommendation_feedback (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    recommendation_id INTEGER REFERENCES job_recommendations(id) ON DELETE CASCADE,

    -- Explicit feedback
    overall_rating INTEGER CHECK (overall_rating >= 1 AND overall_rating <= 5),
    skills_relevance_rating INTEGER CHECK (skills_relevance_rating >= 1 AND skills_relevance_rating <= 5),
    experience_match_rating INTEGER CHECK (experience_match_rating >= 1 AND experience_match_rating <= 5),
    location_rating INTEGER CHECK (location_rating >= 1 AND location_rating <= 5),
    company_interest_rating INTEGER CHECK (company_interest_rating >= 1 AND company_interest_rating <= 5),

    -- Feedback categories
    feedback_type VARCHAR(50) NOT NULL, -- 'positive', 'negative', 'neutral', 'applied', 'saved', 'dismissed'
    feedback_sentiment VARCHAR(20), -- 'very_positive', 'positive', 'neutral', 'negative', 'very_negative'

    -- Text feedback
    feedback_text TEXT,
    improvement_suggestions TEXT,

    -- Implicit signals
    time_spent_viewing INTEGER, -- seconds
    clicked_apply_button BOOLEAN DEFAULT FALSE,
    visited_company_page BOOLEAN DEFAULT FALSE,
    shared_job BOOLEAN DEFAULT FALSE,

    -- Action taken
    action_taken VARCHAR(50), -- 'applied', 'saved', 'dismissed', 'interested', 'not_interested'
    application_status VARCHAR(50), -- 'applied', 'interview_scheduled', 'rejected', 'hired'

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User interaction tracking (implicit feedback)
CREATE TABLE user_interactions (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    recommendation_id INTEGER REFERENCES job_recommendations(id) ON DELETE SET NULL,

    -- Interaction details
    interaction_type VARCHAR(50) NOT NULL, -- 'view', 'click', 'save', 'apply', 'share', 'dismiss'
    interaction_source VARCHAR(50), -- 'recommendation', 'search', 'browse'
    session_id VARCHAR(255),

    -- Context data
    time_spent INTEGER, -- seconds
    scroll_percentage INTEGER, -- how much of job description was viewed
    device_type VARCHAR(50),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- MODEL PERFORMANCE AND LEARNING TABLES
-- ============================================================================

-- Model performance metrics
CREATE TABLE model_performance (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    measurement_date DATE NOT NULL,

    -- Context
    user_segment VARCHAR(100), -- 'all', 'new_users', 'experienced_users', etc.
    job_category VARCHAR(100),

    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT model_performance_unique UNIQUE(model_version, metric_name, measurement_date, user_segment)
);

-- A/B Testing framework
CREATE TABLE ab_test_experiments (
    id SERIAL PRIMARY KEY,
    experiment_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Experiment configuration
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'running', 'completed', 'cancelled'

    -- Test parameters
    control_algorithm_config JSONB,
    test_algorithm_config JSONB,
    traffic_split FLOAT DEFAULT 0.5, -- percentage of users in test group

    -- Success metrics
    primary_metric VARCHAR(100),
    secondary_metrics TEXT[],

    created_at TIMESTAMP DEFAULT NOW()
);

-- User assignment to A/B tests
CREATE TABLE user_ab_assignments (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    experiment_id INTEGER REFERENCES ab_test_experiments(id),
    test_group VARCHAR(50) NOT NULL, -- 'control', 'test'
    assigned_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT user_ab_unique UNIQUE(user_email, experiment_id)
);

-- ============================================================================
-- SUPPORTING TABLES
-- ============================================================================

-- Skills taxonomy for better matching
CREATE TABLE skills_taxonomy (
    id SERIAL PRIMARY KEY,
    skill_name VARCHAR(255) NOT NULL UNIQUE,
    skill_category VARCHAR(100),
    skill_subcategory VARCHAR(100),
    skill_level VARCHAR(50), -- 'beginner', 'intermediate', 'advanced', 'expert'

    -- Relationships
    parent_skill_id INTEGER REFERENCES skills_taxonomy(id),
    related_skills INTEGER[], -- array of skill IDs

    -- Metadata
    skill_description TEXT,
    market_demand_score FLOAT, -- 0.0 to 1.0
    salary_impact_score FLOAT, -- how much this skill affects salary

    -- Embedding for skill similarity
    skill_embedding VECTOR(384),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Company information
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    industry VARCHAR(100),
    size VARCHAR(50),
    location TEXT[],
    website VARCHAR(255),
    rating FLOAT, -- company rating from various sources
    benefits_summary TEXT,
    culture_tags TEXT[],

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Primary lookup indexes
CREATE INDEX idx_jobs_active_posted ON jobs(is_active, posted_date DESC);
CREATE INDEX idx_jobs_company ON jobs(company);
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_experience_level ON jobs(experience_level);
CREATE INDEX idx_jobs_skills_required ON jobs USING GIN(skills_required);

-- User resume indexes
CREATE INDEX idx_user_resumes_email ON user_resumes(user_email);
CREATE INDEX idx_user_resumes_updated ON user_resumes(updated_at DESC);

-- Recommendation indexes
CREATE INDEX idx_job_recommendations_user_score ON job_recommendations(user_email, overall_score DESC);
CREATE INDEX idx_job_recommendations_created ON job_recommendations(created_at DESC);
CREATE INDEX idx_job_recommendations_batch ON job_recommendations(recommendation_batch_id);

-- Feedback indexes
CREATE INDEX idx_recommendation_feedback_user ON recommendation_feedback(user_email);
CREATE INDEX idx_recommendation_feedback_job ON recommendation_feedback(job_id);
CREATE INDEX idx_recommendation_feedback_type ON recommendation_feedback(feedback_type);
CREATE INDEX idx_recommendation_feedback_created ON recommendation_feedback(created_at DESC);

-- Interaction tracking indexes
CREATE INDEX idx_user_interactions_user_created ON user_interactions(user_email, created_at DESC);
CREATE INDEX idx_user_interactions_job ON user_interactions(job_id);
CREATE INDEX idx_user_interactions_type ON user_interactions(interaction_type);

-- Vector similarity indexes (if using pgvector)
-- CREATE INDEX ON jobs USING ivfflat (description_embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX ON user_resumes USING ivfflat (full_resume_embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Update timestamps trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to relevant tables
CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_resumes_updated_at
    BEFORE UPDATE ON user_resumes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recommendation_feedback_updated_at
    BEFORE UPDATE ON recommendation_feedback
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active job recommendations with feedback
CREATE VIEW active_recommendations_with_feedback AS
SELECT
    jr.*,
    j.title as job_title,
    j.company,
    j.location,
    j.salary_min,
    j.salary_max,
    rf.overall_rating,
    rf.feedback_type,
    rf.action_taken
FROM job_recommendations jr
JOIN jobs j ON jr.job_id = j.id
LEFT JOIN recommendation_feedback rf ON jr.id = rf.recommendation_id
WHERE j.is_active = true;

-- User recommendation performance summary
CREATE VIEW user_recommendation_stats AS
SELECT
    user_email,
    COUNT(*) as total_recommendations,
    COUNT(CASE WHEN is_viewed THEN 1 END) as viewed_count,
    COUNT(CASE WHEN is_saved THEN 1 END) as saved_count,
    COUNT(CASE WHEN is_applied THEN 1 END) as applied_count,
    AVG(overall_score) as avg_recommendation_score,
    MAX(created_at) as last_recommendation_date
FROM job_recommendations
GROUP BY user_email;