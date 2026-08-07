BEGIN;

ALTER TABLE project_members
    ALTER COLUMN project_position_id DROP NOT NULL;

UPDATE project_members
SET project_position_id = NULL
WHERE member_type = 'OWNER';

ALTER TABLE project_members
    ADD CONSTRAINT ck_project_members_position_by_type
    CHECK (
        (member_type = 'OWNER' AND project_position_id IS NULL)
        OR
        (member_type = 'MEMBER' AND project_position_id IS NOT NULL)
    );

COMMIT;
