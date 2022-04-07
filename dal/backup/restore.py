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
from zipfile import ZipFile, BadZipFile
from dal.data import scopes
from movai.core import Log


class RestoreJob:
    """
    This class represents a restore job, this
    class is private and should not be
    accessed directly
    """
    _ROOT_PATH = os.path.join(os.getenv('MOVAI_USERSPACE', ""), "restore")

    def __init__(self, restore_file: str):

        if not os.path.exists(restore_file):
            raise ValueError("Restore file does not exists")

        self._job_id = str(uuid.uuid4())
        self._path = os.path.join(RestoreJob._ROOT_PATH, self._job_id)
        self._restore_file = restore_file
        self. _state = {
            "created": int(datetime.now().timestamp()),
            "state": "created"
        }
        os.makedirs(self._path, exist_ok=True)
        shutil.move(restore_file, os.path.join(self._path, "restore.zip"))

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
    def state(self):
        """
        return the state of this job
        """
        return self._state

    def _update_state_file(self):
        state_file = os.path.join(self.path, "state.json")
        with open(state_file, "w") as state_fp:
            return json.dump(self.state, state_fp)

    def run(self):
        """
        starts the restore job
        """
        # This job as already started before ( state_file_created )
        state_file = os.path.join(self.path, "state.json")
        if os.path.exists(state_file):
            RestoreManager.logger.warning(
                "Job previously started, not starting it again: %s", self.job_id)
            return

        RestoreManager.logger.info("Restore job started: %s", self.job_id)
        # we update the state file
        self.state["started"] = int(datetime.now().timestamp())
        self.state["state"] = "started"
        self._update_state_file()

        # setup log and zip archive
        log_file = os.path.join(self.path, "log.txt")
        restore_file = os.path.join(self.path, "restore.zip")

        # Open log, open zip file and process the restore
        with open(log_file, "w") as log_fp:
            try:
                with ZipFile(restore_file, 'r') as archive_fp:

                    try:
                        with archive_fp.open('manifest.json') as manifest_fp:
                            manifest = json.load(manifest_fp)
                        manifest_files = manifest["manifest"]
                    except KeyError as e:
                        log_fp.write(
                            f"[{datetime.now().strftime('%d/%m/%Y-%H:%M')}] Missing manifest!\n")
                        raise BadZipFile from e

                    # start archiving the requested manifest
                    for scope_path in manifest_files:
                        try:
                            scopes.restore(path=scope_path, archive=archive_fp)
                            log_fp.write(
                                f"[{datetime.now().strftime('%d/%m/%Y-%H:%M')}] Scope: {scope_path} restored sucessfully!\n")
                        except (FileNotFoundError, NotImplementedError):
                            log_fp.write(
                                f"[{datetime.now().strftime('%d/%m/%Y-%H:%M')}] Error restoring scope: {scope_path}!\n")
                            continue

            except BadZipFile:
                log_fp.write(
                    f"[{datetime.now().strftime('%d/%m/%Y-%H:%M')}] Invalid zip file!\n")
                RestoreManager.logger.error(
                    "Invalid zip file: %s", self.job_id)

        self.state["finished"] = int(datetime.now().timestamp())
        self.state["state"] = "finished"
        self._update_state_file()
        RestoreManager.logger.info("Restore job finished: %s", self.job_id)

    async def write_log(self, writer):
        """
        writes this restore job log file, this method
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

    def clean(self):
        """
        Clean this restore job, for now we do nothing
        more then delete the restore directory
        """
        shutil.rmtree(self.path, ignore_errors=True)


class RestoreManager:
    """
    A static class to help on interacting with restores
    """
    __RESTORE_JOBS__ = {}
    __EXPIRED_MIN__ = 10
    logger = Log.get_logger("restore.mov.ai")

    @staticmethod
    def create_job(restore_file: str):
        """
        Creates a new restore job
        """
        job = RestoreJob(restore_file)
        RestoreManager.__RESTORE_JOBS__[job.job_id] = job
        return job.job_id

    @staticmethod
    def exists(job_id: str):
        """
        Checks is a job exists
        """
        try:
            return isinstance(RestoreManager.__RESTORE_JOBS__[job_id], RestoreJob)
        except KeyError:
            return os.path.exists(os.path.join(RestoreJob._ROOT_PATH, job_id))

    @staticmethod
    def start_job(job_id: str):
        """
        Runs a restore job, we can only start jobs in our
        session
        """
        try:
            RestoreManager.__RESTORE_JOBS__[job_id].run()
        except KeyError as e:
            raise ValueError("Job not available") from e

    @staticmethod
    def get_job_state(job_id: str):
        """
        Get the state of a job
        """
        try:
            return RestoreManager.__RESTORE_JOBS__[job_id].state
        except KeyError:
            pass

        state_file = os.path.join(RestoreJob._ROOT_PATH, job_id, "state.json")

        # No state.json can't send you nothing
        if not os.path.exists(state_file):
            RestoreManager.logger.error("Restore job not found: %s", job_id)
            raise ValueError("Job does not exists")

        # All good, send the state
        with open(state_file, "r") as state_fp:
            return json.load(state_fp)

    @staticmethod
    def list_jobs():
        """
        Get a list of all existing restore jobs
        """
        jobs_list = set()

        # first we get the jobs that we have
        # registered in this session
        for job in RestoreManager.__RESTORE_JOBS__.values():
            jobs_list.add(job.job_id)

        restore_jobs = glob.glob(os.path.join(
            RestoreJob._ROOT_PATH, "*-*-*-*-*"))

        for job_path in restore_jobs:
            jobs_list.add(os.path.basename(job_path))

        return jobs_list

    @staticmethod
    def clean_jobs():
        """
        Do a clean-up of jobs that had already run successfully,
        this method should be called periodically
        """
        to_delete = []
        RestoreManager.logger.info("Started cleaning up restores")
        # Iterate over all registered jobs and see what
        # jobs had expired
        for job_id in RestoreManager.list_jobs():
            state = RestoreManager.get_job_state(job_id)
            if state["state"] != "finished":
                continue

            # All jobs that have finished more then 10 minutes ago will be
            # clean up and removed
            elapsed = datetime.now() - \
                datetime.fromtimestamp(state["finished"])
            if elapsed.seconds > RestoreManager.__EXPIRED_MIN__ * 60:
                to_delete.append(job_id)

        # Remove all expired jobs from our jobs list
        for job_id in to_delete:
            try:
                # first we remove the ones in cache
                RestoreManager.__RESTORE_JOBS__[job_id].clean()
                del RestoreManager.__RESTORE_JOBS__[job_id]
                continue
            except KeyError:
                pass

            # otherwise remove the ones in disk
            job_path = os.path.join(RestoreJob._ROOT_PATH, job_id)
            shutil.rmtree(job_path, ignore_errors=True)

        RestoreManager.logger.info("Restore clean complete")

    @staticmethod
    async def write_log(job_id: str, writer):
        """
        writes this restore job log file, this method
        does not read everthing to memory, instead
        it reads the content of the file direct to
        a write
        """
        try:
            await RestoreManager.__RESTORE_JOBS__[job_id].write_log(writer)
            return
        except KeyError:
            pass

        log_file = os.path.join(RestoreJob._ROOT_PATH, job_id, "log.txt")

        # No log.txt? can't send you nothing
        if not os.path.exists(log_file):
            RestoreManager.logger.error("Restore job not found: %s", job_id)
            raise ValueError("Job not found")

        # All good, send the log file
        with open(log_file, "rb") as file:
            buffer = file.read(2 ** 16)
            while buffer:
                await writer.write(buffer)
                buffer = file.read(2 ** 16)
