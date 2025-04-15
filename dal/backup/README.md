# Mov.ai Backup Module

This is part of Mov.ai and is responsible for implemening the logic behind Backup/Restore of data.

## Implementation

Currently we implement 4 classes:
- BackupJob
- RestoreJob
- BackupManager
- RestoreManager

## Implementation Notes

- Each xxxxJob class represents a Job that was created by the xxxxManager
- Each Job is related to a folder in the filesystem
- The location on the filesystem is: ```_ROOT_PATH = os.path.join(os.getenv('MOVAI_USERSPACE', ""), "backups|restore")```
- Each xxxxJob have an unique id (uuid4) which matches the folder name
- Each xxxxJob have a state file ```state.json```
- Each xxxxJob have a log file
- BackupJob requires a list of scopes to backup, metadata and shallow flag is optional, ```create_job(manifest: list, shallow: bool = True, metadata: dict = None)```
- BackupJob create a file called ```backup.zip```
- RestoreJob requires the location of a restore file, ```create_job(restore_file: str)```
- RestoreJob copy the restore file into the Job folder ```restore.zip```
- Each manager have a clean function which deletes jobs with more than ```__EXPIRED_MIN__ = 10```, ```clean_jobs()```

## Code Snippets

### Using BackupManager
```
from dal.backup import BackupManager

# Creates a new backup job
job_id = BackupManager.create_job(manifest=["global/Flow/mapping/__UNVERSIONED__"])

# Starts the job
BackupManager.start_job(job_id)

# Write the archive into another file
with open("/tmp/backup.zip", "wb") as f:
    BackupManager.write_archive(job_id, f)

# Write the log into file
with open("/tmp/backup.log", "wb") as f:
    BackupManager.write_log(job_id, f)
```

### Using RestoreManager
```
from dal.backup import RestoreManager

# Creates a new restore job
job_id = RestoreManager.create_job(restore_file='/tmp/backup.zip')

# Starts the job
RestoreManager.start_job(job_id)

# Write the log into file
with open("/tmp/restore.log", "w") as f:
    RestoreManager.write_log(job_id, f)
```
