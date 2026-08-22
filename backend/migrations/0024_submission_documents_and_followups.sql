-- Migration 0024: submission document uploads, proof of submission/response,
-- and a follow-up log for government submissions.
--
-- Backs the redesigned submission workflow:
--   1. In Draft, each Required Document can be uploaded as it becomes
--      available (submission_documents gains storage_key/original_filename/
--      file_size_bytes/uploaded_by/upload_date -- same shape as
--      project_documents).
--   2. Once every required document is Uploaded/Verified, Proof of
--      Submission (a document upload) is recorded on the submission itself
--      and the submission moves Draft -> Submitted.
--   3. While awaiting a decision, follow-up calls/visits are logged
--      (new submission_followups table -- date, time, contact person).
--   4. When the authority responds, Proof of Response is uploaded along
--      with an outcome (Approved/Rejected); an Approved outcome allows the
--      submission to be marked complete.
--
-- Idempotent -- guarded by information_schema checks, same convention as
-- every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0024_submission_documents_and_followups.sql

-- --- submission_documents: file fields -------------------------------

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'submission_documents' AND COLUMN_NAME = 'storage_key'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE submission_documents
     ADD COLUMN storage_key VARCHAR(300) NULL AFTER status,
     ADD COLUMN original_filename VARCHAR(255) NULL AFTER storage_key,
     ADD COLUMN file_size_bytes BIGINT UNSIGNED NULL AFTER original_filename,
     ADD COLUMN uploaded_by BIGINT UNSIGNED NULL AFTER file_size_bytes,
     ADD COLUMN upload_date DATE NULL AFTER uploaded_by,
     ADD CONSTRAINT fk_submission_documents_uploaded_by FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- --- government_submissions: proof of submission / proof of response --

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'government_submissions' AND COLUMN_NAME = 'proof_of_submission_storage_key'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE government_submissions
     ADD COLUMN proof_of_submission_storage_key VARCHAR(300) NULL AFTER notes,
     ADD COLUMN proof_of_submission_filename VARCHAR(255) NULL AFTER proof_of_submission_storage_key,
     ADD COLUMN proof_of_submission_size_bytes BIGINT UNSIGNED NULL AFTER proof_of_submission_filename,
     ADD COLUMN proof_of_submission_uploaded_by BIGINT UNSIGNED NULL AFTER proof_of_submission_size_bytes,
     ADD COLUMN proof_of_submission_upload_date DATE NULL AFTER proof_of_submission_uploaded_by,
     ADD COLUMN proof_of_response_storage_key VARCHAR(300) NULL AFTER proof_of_submission_upload_date,
     ADD COLUMN proof_of_response_filename VARCHAR(255) NULL AFTER proof_of_response_storage_key,
     ADD COLUMN proof_of_response_size_bytes BIGINT UNSIGNED NULL AFTER proof_of_response_filename,
     ADD COLUMN proof_of_response_uploaded_by BIGINT UNSIGNED NULL AFTER proof_of_response_size_bytes,
     ADD COLUMN proof_of_response_upload_date DATE NULL AFTER proof_of_response_uploaded_by,
     ADD COLUMN response_outcome ENUM(''Approved'',''Rejected'') NULL AFTER proof_of_response_upload_date,
     ADD CONSTRAINT fk_government_submissions_proof_submission_by FOREIGN KEY (proof_of_submission_uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
     ADD CONSTRAINT fk_government_submissions_proof_response_by FOREIGN KEY (proof_of_response_uploaded_by) REFERENCES users(id) ON DELETE RESTRICT',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- --- submission_followups: new table -----------------------------------

CREATE TABLE IF NOT EXISTS submission_followups (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    submission_id   BIGINT UNSIGNED NOT NULL,
    followup_date   DATE NOT NULL,
    followup_time   VARCHAR(20) NOT NULL,
    contact_person  VARCHAR(150) NOT NULL,
    notes           TEXT NULL,
    created_by      BIGINT UNSIGNED NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_submission_followups_submission FOREIGN KEY (submission_id) REFERENCES government_submissions(id) ON DELETE CASCADE,
    CONSTRAINT fk_submission_followups_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_submission_followups_submission (submission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT 'Migration 0024 complete.' AS status;
