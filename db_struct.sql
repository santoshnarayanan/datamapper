-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. WORKFLOW
CREATE TABLE workflow (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_email TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. WORKSHEET
CREATE TABLE worksheet (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL,
    name TEXT,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_workflow
        FOREIGN KEY(workflow_id)
        REFERENCES workflow(id)
        ON DELETE CASCADE
);

-- Index for faster lookups
CREATE INDEX idx_worksheet_workflow_id ON worksheet(workflow_id);

-- 3. DATAPREPARE
CREATE TABLE dataprepare (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL,
    worksheet_id UUID NOT NULL,
    steps JSONB,        -- transformation steps
    snapshots JSONB,    -- optional snapshots
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_dp_workflow
        FOREIGN KEY(workflow_id)
        REFERENCES workflow(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_dp_worksheet
        FOREIGN KEY(worksheet_id)
        REFERENCES worksheet(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_dataprepare_workflow_id ON dataprepare(workflow_id);
CREATE INDEX idx_dataprepare_worksheet_id ON dataprepare(worksheet_id);

-- 4. EBATEMPLATE
CREATE TABLE ebatemplate (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    structure JSONB NOT NULL
);

-- Optional index if you query structure
CREATE INDEX idx_ebatemplate_structure ON ebatemplate USING GIN (structure);

-- 5. MAPPINGINFO
CREATE TABLE mappinginfo (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL,
    mapping JSONB NOT NULL,

    CONSTRAINT fk_mapping_workflow
        FOREIGN KEY(workflow_id)
        REFERENCES workflow(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_mappinginfo_workflow_id ON mappinginfo(workflow_id);
CREATE INDEX idx_mappinginfo_mapping ON mappinginfo USING GIN (mapping);



ALTER TABLE worksheet ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE dataprepare ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE mappinginfo ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;