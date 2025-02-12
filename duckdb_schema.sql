-- ============================================
-- Table: users
-- Stores details for each user (e.g., created_by, changed_by, assigned_to).
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR PRIMARY KEY,  -- Azure DevOps unique user identifier.
    display_name TEXT,
    unique_name TEXT,
    image_url TEXT,
    descriptor TEXT
);

-- ============================================
-- Table: work_items
-- Stores the main work item (ticket) information.
-- ============================================
CREATE TABLE IF NOT EXISTS work_items (
    id INTEGER PRIMARY KEY,  -- Corresponds to System.Id
    work_item_type TEXT,     -- e.g. Bug, Task, User Story
    title TEXT,
    state TEXT,
    reason TEXT,
    created_date TIMESTAMP,
    created_by_id VARCHAR,   -- References users(user_id)
    changed_date TIMESTAMP,
    changed_by_id VARCHAR,   -- References users(user_id)
    assigned_to_id VARCHAR,  -- References users(user_id); if available.
    area_path TEXT,
    iteration_path TEXT,
    team_project TEXT,
    description TEXT,
    comment_count INTEGER,
    -- Scheduling / Estimation fields:
    story_points REAL,
    original_estimate REAL,
    remaining_work REAL,
    completed_work REAL,
    target_date TIMESTAMP,
    prod_release_date TIMESTAMP,  -- Typically the closed date.
    actual_release_date TIMESTAMP,  -- Typically the resolved date.
    environment TEXT,
    root_cause TEXT,
    found_in_environment TEXT,
    facility TEXT,
    activated_date TIMESTAMP,
    activated_by_id VARCHAR,  -- References users(user_id)
    -- Store any extra/unmodeled fields as JSON.
    extra_fields JSON
);

-- ============================================
-- Optional: Table: work_item_tags
-- Normalizes tags associated with a work item.
-- ============================================
CREATE TABLE IF NOT EXISTS work_item_tags (
    work_item_id INTEGER,  -- References work_items(id)
    tag TEXT,
    PRIMARY KEY (work_item_id, tag)
);

-- ============================================
-- Table: revisions
-- Stores each revision (snapshot) of a work item.
-- ============================================
CREATE TABLE IF NOT EXISTS revisions (
    revision_id INTEGER PRIMARY KEY,  -- Use DuckDB's auto-increment behavior.
    work_item_id INTEGER,             -- References work_items(id)
    rev INTEGER,                      -- Revision number (e.g., System.Rev)
    changed_date TIMESTAMP,
    state TEXT,                       -- System.State at this revision.
    reason TEXT,                      -- System.Reason at this revision.
    title TEXT,                       -- Title at this revision (if desired).
    assigned_to_id VARCHAR,           -- Can capture the assigned user at this revision.
    -- Optionally store the full snapshot of fields as JSON.
    fields_snapshot JSON
);

-- ============================================
-- Table: comments
-- Stores important comment data for a work item.
-- ============================================
CREATE TABLE IF NOT EXISTS comments (
    comment_id INTEGER PRIMARY KEY,  -- Azure DevOps provided comment id.
    work_item_id INTEGER,            -- References work_items(id)
    rev INTEGER,                     -- Revision number when the comment was added (if applicable).
    comment_type TEXT,               -- e.g., text, etc.
    state TEXT,                      -- Typically "active".
    text TEXT,                       -- The full comment text.
    created_date TIMESTAMP,
    created_by_id VARCHAR,           -- References users(user_id).
    modified_date TIMESTAMP,
    modified_by_id VARCHAR,          -- References users(user_id).
    -- Store any additional comment information as JSON.
    extra_fields JSON
); 