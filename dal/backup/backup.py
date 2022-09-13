"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
import json
import os
import uuid
import glob
import shutil
from datetime import datetime
from zipfile import ZipFile

from movai_core_shared.logger import Log
from dal.scopes.scopestree import ScopesTree, scopes
from dal.models.model import Model



class BackupJob:
    """
    This class represents a backup job, this
    class is private and should not be
    accessed directly
    """
    _ROOT_PATH = os.path.join(os.getenv('MOVAI_USERSPACE', ""), "backups")

    def __init__(self, manifest: list, shallow: bool = False, metadata: dict = None):
        self._job_id = str(uuid.uuid4())
        self._path = os.path.join(BackupJob._ROOT_PATH, self._job_id)
        self._manifest = manifest
        self._shallow = shallow
        self._metadata = metadata
        self. _state = {
            "created": int(datetime.now().timestamp()),
            "state": "created"
        }
        os.makedirs(self._path, exist_ok=True)

    @property
    def job_id(self):
        """
        return the curren job id
        """
        return self._job_id

    @property
    def path(self):
        """
        return the path of this job
        """
        return self._path

    @property
    def manifest(self):
        """
        return the manifest of this job
        """
        return self._manifest

    @property
    def state(self):
        """
        return the state of this job
        """
        return self._state

    @property
    def metadata(self):
        """
        return the metadata for this job
        """
        return self._metadata

    def _update_state_file(self):
        state_file = os.path.join(self.path, "state.json")
        with open(state_file, "w") as state_fp:
            return json.dump(self.state, state_fp)

    def run(self):
        """
        starts the backup job
        """
        # This job as already started before ( state_file_created )
        state_file = os.path.join(self.path, "state.json")
        if os.path.exists(state_file):
            BackupManager.logger.warning("Job previously started, not starting it again: %s", self.job_id)
            return

        BackupManager.logger.info("Backup job started: %s", self.job_id)
        # we update the state file
        self.state["started"] = int(datetime.now().timestamp())
        self.state["state"] = "started"
        self._update_state_file()

        # setup log and zip archive
        log_file = os.path.join(self.path, "log.txt")
        backup_file = os.path.join(self.path, "backup.zip")
        manifest_file = "manifest.json"
        depth = 0 if self._shallow else 99

        # Open log, open zip file and process the manifest
        with open(log_file, "w") as log_fp:
            with ZipFile(backup_file, 'w') as archive_fp:

                # start archiving the requested manifest
                archived_scopes = set()

                for scope_path in self.manifest:
                    try:
                        scopes.backup(path=scope_path, archive=archive_fp)
                        archived_scopes.add(scope_path)
                        log_fp.write(
                            f"[{datetime.now().strftime('%d/%m/%Y-%H:%M')}] Scope: {scope_path} archived sucessfully!\n")
                    except (FileNotFoundError, NotImplementedError):
                        log_fp.write(
                            f"[{datetime.now().strftime('%d/%m/%Y-%H:%M')}] Error archiving scope: {scope_path}!\n")
                        continue

                    log_fp.write(
                        f"[{datetime.now().strftime('%d/%m/%Y-%H:%M')}] Looking for scope: {scope_path} dependencies!\n")

                    # Scope done, next we process the dependencies, if we selected a shallow archive we just process
                    # the direct dependencies, depth = 0
                    workspace, scope, ref, version = ScopesTree.extract_reference(
                        scope_path)

                    dependencies = Model.get_relations(
                        workspace=workspace, scope=scope, ref=ref, version=version, depth=depth)

                    # store each dependencie
                    for dependency in dependencies:

                        try:
                            scopes.backup(path=dependency, archive=archive_fp)
                            archived_scopes.add(dependency)
                            log_fp.write(
                                f"[{datetime.now().strftime('%d/%m/%Y-%H:%M')}] Dependency scope: {dependency} archived sucessfully!\n")
                        except (FileNotFoundError, NotImplementedError):
                            log_fp.write(
                                f"[{datetime.now().strftime('%d/%m/%Y-%H:%M')}] Error archiving dependency scope: {dependency}!\n")
                            continue

                # store manifest file inside our archive, for now we
                # store simple information like the metada, creation date, and the
                # list of all scopes added, maybe in the future it will be required
                # to add some security features
                log_fp.write(
                    f"[{datetime.now().strftime('%d/%m/%Y-%H:%M')}] Writing archive manifest\n")
                archive_fp.writestr(manifest_file, json.dumps(
                    {
                        "metadata": self._metadata,
                        "date": datetime.now().strftime('%d/%m/%Y-%H:%M'),
                        "manifest": list(archived_scopes)
                    }))

            log_fp.write(
                f"[{datetime.now().strftime('%d/%m/%Y-%H:%M')}] Archive finished!\n")

        self.state["finished"] = int(datetime.now().timestamp())
        self.state["state"] = "finished"
        self._update_state_file()
        BackupManager.logger.info("Backup job finished: %s", self.job_id)

    async def write_log(self, writer):
        """
        writes this backup job log file, this method
        does not read everthing to memory, instead
        it reads the content of the file direct to
        a write
        """
        log_file = os.path.join(self.path, "log.txt")

        # No log.txt? can't send you nothing
        if not os.path.exists(log_file):
            raise FileNotFoundError

        # All good, send the log file
        with open(log_file, "rb") as file:
            buffer = file.read(2 ** 16)
            while buffer:
                await writer.write(buffer)
                buffer = file.read(2 ** 16)

    async def write_archive(self, writer):
        """
        return this backup file, this method
        does not read everthing to memory, instead
        it reads the content of the file direct to
        a write
        """
        state = self._state["state"]

        # if we didn't finished yet the backup we can't send the
        # archive
        if state != "finished":
            raise FileNotFoundError

        backup_file = os.path.join(self.path, "backup.zip")

        # If this happen something is really wrong!!!
        if not os.path.exists(backup_file):
            raise FileNotFoundError

        # All good, send the archive file
        with open(backup_file, "rb") as file:
            buffer = file.read(2 ** 16)
            while buffer:
                await writer.write(buffer)
                buffer = file.read(2 ** 16)

    def clean(self):
        """
        Clean this backup job, for now we do nothing
        more then delete the backup directory
        """
        shutil.rmtree(self.path, ignore_errors=True)


class BackupManager:
    """
    A static class to help on interacting with backups
    """
    __BACKUP_JOBS__ = {}
    __EXPIRED_MIN__ = 10
    logger = Log.get_logger("backup.mov.ai")

    @staticmethod
    def create_job(manifest: list, shallow: bool = True, metadata: dict = None):
        """
        Creates a new backup job
        """
        job = BackupJob(manifest, shallow, metadata)
        BackupManager.__BACKUP_JOBS__[job.job_id] = job
        return job.job_id

    @staticmethod
    def exists(job_id: str):
        """
        Checks is a job exists
        """
        try:
            return isinstance(BackupManager.__BACKUP_JOBS__[job_id], BackupJob)
        except KeyError:
            return os.path.exists(os.path.join(BackupJob._ROOT_PATH, job_id))

    @staticmethod
    def start_job(job_id: str):
        """
        Runs a backup job, we can only start jobs in our
        session
        """
        try:
            BackupManager.__BACKUP_JOBS__[job_id].run()
        except KeyError as e:
            raise ValueError("Job not available") from e

    @staticmethod
    def get_job_state(job_id: str):
        """
        Get the state of a job
        """
        try:
            return BackupManager.__BACKUP_JOBS__[job_id].state
        except KeyError:
            pass

        state_file = os.path.join(BackupJob._ROOT_PATH, job_id, "state.json")

        # No state.json can't send you nothing
        if not os.path.exists(state_file):
            BackupManager.logger.error("Backup job not found: %s", job_id)
            raise ValueError("Job does not exists")

        # All good, send the state
        with open(state_file, "r") as state_fp:
            return json.load(state_fp)

    @staticmethod
    def list_jobs():
        """
        Get a list of all existing backup jobs
        """
        jobs_list = set()

        # first we get the jobs that we have
        # registered in this session
        for job in BackupManager.__BACKUP_JOBS__.values():
            jobs_list.add(job.job_id)

        backup_jobs = glob.glob(os.path.join(
            BackupJob._ROOT_PATH, "*-*-*-*-*"))

        for job_path in backup_jobs:
            jobs_list.add(os.path.basename(job_path))

        return jobs_list

    @staticmethod
    def clean_jobs():
        """
        Do a clean-up of jobs that had already run successfully,
        this method should be called periodically
        """
        to_delete = []
        BackupManager.logger.info("Started cleaning up backups")
        # Iterate over all registered jobs and see what
        # jobs had expired
        for job_id in BackupManager.list_jobs():
            state = BackupManager.get_job_state(job_id)
            if state["state"] != "finished":
                continue

            # All jobs that have finished more then 10 minutes ago will be
            # clean up and removed
            elapsed = datetime.now() - \
                datetime.fromtimestamp(state["finished"])
            if elapsed.seconds > BackupManager.__EXPIRED_MIN__ * 60:
                to_delete.append(job_id)

        # Remove all expired jobs from our jobs list
        for job_id in to_delete:
            try:
                # first we remove the ones in cache
                BackupManager.__BACKUP_JOBS__[job_id].clean()
                del BackupManager.__BACKUP_JOBS__[job_id]
                continue
            except KeyError:
                pass

            # otherwise remove the ones in disk
            job_path = os.path.join(BackupJob._ROOT_PATH, job_id)
            shutil.rmtree(job_path, ignore_errors=True)

        BackupManager.logger.info("Backup clean complete")

    @staticmethod
    async def write_log(job_id: str, writer):
        """
        writes this backup job log file, this method
        does not read everthing to memory, instead
        it reads the content of the file direct to
        a write
        """
        try:
            await BackupManager.__BACKUP_JOBS__[job_id].write_log(writer)
            return
        except KeyError:
            pass

        log_file = os.path.join(BackupJob._ROOT_PATH, job_id, "log.txt")

        # No log.txt? can't send you nothing
        if not os.path.exists(log_file):
            BackupManager.logger.error("Backup job not found: %s", job_id)
            raise ValueError("Job not found")

        # All good, send the log file
        with open(log_file, "rb") as file:
            buffer = file.read(2 ** 16)
            while buffer:
                await writer.write(buffer)
                buffer = file.read(2 ** 16)

    @staticmethod
    async def write_archive(job_id: str, writer):
        """
        writes this backup job archive, this method
        does not read everthing to memory, instead
        it reads the content of the file direct to
        a write
        """
        try:
            await BackupManager.__BACKUP_JOBS__[job_id].write_archive(writer)
            return
        except KeyError:
            pass

        backup_file = os.path.join(BackupJob._ROOT_PATH, job_id, "backup.zip")

        # No backup.zip? can't send you nothing
        if not os.path.exists(backup_file):
            BackupManager.logger.error("Backup job not found: %s", job_id)
            raise ValueError("Job not found")

        # All good, send the log file
        with open(backup_file, "rb") as file:
            buffer = file.read(2 ** 16)
            while buffer:
                await writer.write(buffer)
                buffer = file.read(2 ** 16)
