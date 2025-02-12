PRAGMA foreign_keys = ON;

-- ============================================
-- Table: users
-- Stores user details referenced by work items and revisions.
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,           -- e.g. the GUID from System.CreatedBy, System.ChangedBy, etc.
    display_name TEXT,
    url TEXT,
    unique_name TEXT,
    image_url TEXT,
    descriptor TEXT
);

-- ============================================
-- Table: work_items
-- Stores the main work item (ticket) information.
-- Note: The "tags" column has been removed.
-- ============================================
CREATE TABLE IF NOT EXISTS work_items (
    id INTEGER PRIMARY KEY,                   -- Corresponds to System.Id
    work_item_type TEXT,                      -- E.g. Bug, Task, User Story
    title TEXT,
    state TEXT,
    reason TEXT,
    history TEXT,
    created_date TEXT,                        -- System.CreatedDate (ISO8601 format)
    changed_date TEXT,                        -- System.ChangedDate
    comment_count INTEGER,
    team_project TEXT,
    area_path TEXT,
    area_id INTEGER,
    area_level1 TEXT,
    area_level2 TEXT,
    iteration_path TEXT,
    iteration_id INTEGER,
    iteration_level1 TEXT,
    iteration_level2 TEXT,
    iteration_level3 TEXT,
    iteration_level4 TEXT,
    parent INTEGER,
    story_points REAL,                        -- Microsoft.VSTS.Scheduling.StoryPoints
    original_estimate REAL,                   -- Microsoft.VSTS.Scheduling.OriginalEstimate
    remaining_work REAL,                      -- Microsoft.VSTS.Scheduling.RemainingWork
    completed_work REAL,                      -- Microsoft.VSTS.Scheduling.CompletedWork (if available)
    priority INTEGER,                         -- Microsoft.VSTS.Common.Priority
    stack_rank REAL,                          -- Microsoft.VSTS.Common.StackRank
    watermark INTEGER,
    person_id INTEGER,
    state_change_date TEXT,
    activated_date TEXT,
    closed_date TEXT,
    custom_work TEXT,
    description TEXT,
    created_by_id TEXT,                       -- From System.CreatedBy
    changed_by_id TEXT,                       -- From System.ChangedBy
    authorized_as_id TEXT,                    -- From System.AuthorizedAs
    assigned_to_id TEXT,                      -- From System.AssignedTo
    extra_fields TEXT,                        -- Stores any extra/unmodeled fields as JSON
    FOREIGN KEY(created_by_id) REFERENCES users(id),
    FOREIGN KEY(changed_by_id) REFERENCES users(id),
    FOREIGN KEY(authorized_as_id) REFERENCES users(id),
    FOREIGN KEY(assigned_to_id) REFERENCES users(id)
);

-- ============================================
-- Table: work_item_tags
-- A separate table that maps each work item to one or more tags.
-- ============================================
CREATE TABLE IF NOT EXISTS work_item_tags (
    work_item_id INTEGER,
    tag TEXT,
    PRIMARY KEY (work_item_id, tag),
    FOREIGN KEY(work_item_id) REFERENCES work_items(id)
);

-- ============================================
-- Table: revisions
-- Captures each revision (snapshot) of a work item.
-- (Optional: Remove "tags" from revisions if not needed here.)
-- ============================================
CREATE TABLE IF NOT EXISTS revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_item_id INTEGER,                     -- References work_items(id)
    rev INTEGER,                              -- System.Rev
    area_id INTEGER,                          -- System.AreaId
    node_name TEXT,                           -- System.NodeName
    area_level1 TEXT,                         -- System.AreaLevel1
    iteration_id INTEGER,                     -- System.IterationId
    iteration_level1 TEXT,                    -- System.IterationLevel1
    iteration_level2 TEXT,                    -- System.IterationLevel2
    iteration_level3 TEXT,                    -- System.IterationLevel3
    iteration_level4 TEXT,                    -- System.IterationLevel4
    work_item_type TEXT,                      -- System.WorkItemType
    state TEXT,                               -- System.State
    reason TEXT,                              -- System.Reason
    assigned_to_id TEXT,                      -- From System.AssignedTo in this revision
    created_date TEXT,                        -- System.CreatedDate
    created_by_id TEXT,                       -- From System.CreatedBy
    changed_date TEXT,                        -- System.ChangedDate
    changed_by_id TEXT,                       -- From System.ChangedBy
    authorized_date TEXT,                     -- System.AuthorizedDate
    revised_date TEXT,                        -- System.RevisedDate
    authorized_as_id TEXT,                    -- From System.AuthorizedAs
    person_id INTEGER,                        -- System.PersonId
    watermark INTEGER,                        -- System.Watermark
    comment_count INTEGER,                    -- System.CommentCount
    team_project TEXT,                        -- System.TeamProject
    area_path TEXT,                           -- System.AreaPath
    iteration_path TEXT,                      -- System.IterationPath
    title TEXT,                               -- System.Title
    story_points REAL,                        -- Microsoft.VSTS.Scheduling.StoryPoints
    original_estimate REAL,                   -- Microsoft.VSTS.Scheduling.OriginalEstimate
    remaining_work REAL,                      -- Microsoft.VSTS.Scheduling.RemainingWork
    completed_work REAL,                      -- Microsoft.VSTS.Scheduling.CompletedWork (if available)
    closed_date TEXT,                         -- Microsoft.VSTS.Common.ClosedDate
    closed_by_id TEXT,                        -- From Microsoft.VSTS.Common.ClosedBy
    priority INTEGER,                         -- Microsoft.VSTS.Common.Priority
    stack_rank REAL,                          -- Microsoft.VSTS.Common.StackRank
    FOREIGN KEY(work_item_id) REFERENCES work_items(id),
    FOREIGN KEY(assigned_to_id) REFERENCES users(id),
    FOREIGN KEY(created_by_id) REFERENCES users(id),
    FOREIGN KEY(changed_by_id) REFERENCES users(id),
    FOREIGN KEY(authorized_as_id) REFERENCES users(id),
    FOREIGN KEY(closed_by_id) REFERENCES users(id)
);

-- ============================================
-- Table: comments
-- Optionally stores comment data for work items.
-- ============================================
CREATE TABLE IF NOT EXISTS comments (
    comment_id INTEGER PRIMARY KEY,
    work_item_id INTEGER,
    rev INTEGER,                              -- Revision number when the comment was added
    comment_type TEXT,                        -- E.g., "text" or other data
    state TEXT,                               -- Comment state (if applicable)
    text TEXT,                                -- Full comment text
    created_date TEXT,                        -- When the comment was created
    created_by_id TEXT,                       -- Which user created it
    modified_date TEXT,                       -- If modified, when
    modified_by_id TEXT,                      -- User who modified it
    FOREIGN KEY(work_item_id) REFERENCES work_items(id),
    FOREIGN KEY(created_by_id) REFERENCES users(id),
    FOREIGN KEY(modified_by_id) REFERENCES users(id)
);

-- Add the iterations metadata table
CREATE TABLE IF NOT EXISTS iterations (
    iteration_id INTEGER PRIMARY KEY,  -- Azure DevOps iteration ID
    name TEXT,
    path TEXT,
    start_date TEXT,
    finish_date TEXT,
    timeframe TEXT
);