"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
   - Moawiya Mograbi (moawiya@mov.ai) - 2021

   Module for users to use locks with redis
"""
import asyncio
import time
import redis

from dal.movaidb.database import MovaiDB
# from deprecated.api.exceptions.exceptions import MovaiException
# from deprecated.logger import StdoutLogger
# from .robot import Robot

SCOPES = ['local', 'global']

# logger = StdoutLogger('Lock')


class Lock:
    """Class for user to acquire and release locks

        Args:
            name: Name of the key to lock
            scope: The lock can be used in "global" or "local" scopes
            timeout: Maximum life for the lock in seconds (float or integer)
            blocking_timeout: Maximum amount of time to spend trying
                              to acquire the lock
            queue_level: Priority level (1-5) to be added to the queue.
                         None to not go to queue
            persistent: persist after the flow is stopped
    """

    enabled_locks = []
    HEARTBEAT_MIN_TIMEOUT = 1
    DEFAULT_MAX_RETRIES = 3  # nr. of times we try to reacquire the lock
    HEARTBEAT_FREQ_FACTOR = 0.25
    DEFAULT_LOCK_TIMEOUT = 90

    def __init__(self, name: str, scope: str = 'global', *, timeout: float = 0,
                 queue_level: int = None, blocking_timeout: float = 0,
                 alive_timeout: float = 5000, robot_name: str = None,
                 node_name: str = 'test_node', persistent: bool = False,
                 reacquire: bool = False):
        """initialize the Lock object

        Args:
            name (str): name of the lock
            scope (str, optional): scope. Defaults to 'global'.
            timeout (float, optional): timeoue which the lock will be
                                       freed after. Defaults to 0.
            queue_level (int, optional): [description]. Defaults to None.
            blocking_timeout (float, optional): indicates the maximum amount of
                                            time in seconds to spend trying
                                            to acquire the lock. Defaults to 0.
            alive_timeout (float, optional): [description]. Defaults to 5000.
            _robot_name (str, optional): the robot name which created the lock.
                                         Defaults to None.
            _node_name (str, optional): the node name which we created the node
                                        form. Defaults to 'test_node'.
            persistent (bool, optional): if set to True the lock will be
                                         remained locked even after
                                         spawner dies. Defaults to False.
            reacquire (bool, optional): should we reacquire the lock in the
                                        heartbeat. Defaults to False.

        Raises:
            MovaiException: in case it's not a valid scope
        """
        if scope not in SCOPES:
            # TODO, MoviaException
            raise Exception(f"'{scope}' is not a valid scope. \
                                 Choose between: '{str(SCOPES)[1:-1]}")

        self.db_read = MovaiDB(scope).db_read
        self.db_write = MovaiDB(scope).db_write

        self._name = name
        self.scope = scope
        self.lock_name = f"Lock:{name},Value:"
        self.queue_name = f"Lock:{name},Queue:"
        self.alive_name = f"Lock:{name},Alive:"
        self.persistent = persistent

        self.queue_level = queue_level
        self.timeout = timeout
        self.alive_timeout = alive_timeout
        self.robot_name = robot_name
        # or Robot().name
        self.node_name = node_name

        self.source = self.robot_name if scope == 'global' else self.node_name

        self.blocking_timeout = blocking_timeout
        self.should_reacquire = reacquire
        if timeout == 0:
            # default timeout time
            timeout = self.DEFAULT_LOCK_TIMEOUT
            self.should_reacquire = True
        self.db_lock = self.db_write.lock(self.lock_name, timeout=timeout,
                                          blocking_timeout=blocking_timeout,
                                          thread_local=False)

        if not isinstance(self.source, bytes):
            # needed for db_lock.owned(), redis-py lock owned() method
            # assumes that local.token is in bytes.
            encoder = self.db_lock.redis.connection_pool.get_encoder()
            if encoder:
                self.db_lock.local.token = encoder.encode(self.source)
            else:
                self.db_lock.local.token = self.source.encode()

    def __enter__(self):
        self.acquire(blocking=True)

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    def acquire(self, blocking=None) -> bool:
        """
        function to quire the lock
        Args:
            blocking: indicates whether calling ``acquire`` should block until
                      the lock has been acquired or to fail immediately,
                      causing ``acquire`` to return False and the lock not
                      being acquired.

        Returns: True, succeeded to acquire
        """

        if self.is_owned():
            # logger.warning(f"Lock {self._name} already owned")
            return True

        res = False
        stop_trying_at = None
        start_time = time.time()
        time_milis = int(start_time * 1000)

        if self.queue_level:  # Add me to the queue and to the alive
            try:
                score = int(str(self.queue_level) + str(time_milis))
                self.db_write.zadd(self.queue_name, {self.source: score},
                                   nx=True)
                self.db_write.zadd(self.alive_name, {self.source: time_milis})

            except Exception as e:
                #logger.error(f"Could not add to queue {self._name} in \
                #             {self.source}. see error: {e}")
                pass

        if self.blocking_timeout is not None and not blocking:
            stop_trying_at = start_time + self.blocking_timeout

        while True:
            # Here we remove the guys in from of me that are not alive-cuz Yolo
            # First get all elements with score lower than mine
            my_score = self.db_read.zscore(self.queue_name, self.source)
            my_score = my_score - 1 if my_score else '+inf'
            frontline = self.db_read.zrangebyscore(
                self.queue_name, '-inf', my_score)

            # then check the last time they were alive
            for elem in frontline:
                elem_name = elem.decode('utf-8')
                last_alive = self.db_read.zscore(self.alive_name, elem_name)
                if int(time.time() * 1000) - last_alive > self.alive_timeout:
                    # logger.debug(
                    #    f'{elem_name} removed from queue for inactivity')
                    try:
                        self.db_write.zrem(self.queue_name, elem_name)
                        self.db_write.zrem(self.alive_name, elem_name)

                    except Exception as e:
                        # logger.error(f"Could not remove {elem_name} from \
                        #             queue {self._name}. see error: {e}")
                        pass

            # return the first guy in the queue (lowest score)
            lowest_score_robot = self.db_read.zrange(self.queue_name, 0, 0)

            if not lowest_score_robot \
               or lowest_score_robot[0].decode('utf-8') == self.source:
                # No one in queue or its me!!!
                block_inside = self.blocking_timeout - \
                               (time.time() - start_time)
                res = self.db_lock.acquire(
                                           blocking=blocking,
                                           blocking_timeout=block_inside,
                                           token=self.source)
                if res:
                    # We acquired the lock so lets remove us from
                    # queue and alive
                    try:
                        self.db_write.zrem(self.queue_name, self.source)
                        self.db_write.zrem(self.alive_name, self.source)

                    except Exception as e:
                        # TODO
                        #logger.error(f"Could not remove from queue \
                        #             {self._name} in {self.source}. \
                        #             see error: {e}")
                        pass

                    # enable Lock heartbeat
                    self.send_lock_cmd()
                    break

            if stop_trying_at is not None and time.time() > stop_trying_at:
                res = False
                break

            asyncio.sleep(0.1)

        return res

    def release(self) -> bool:
        """
        Releases the already acquired lock.

        Returns:
            False if lock not owned
        """
        try:
            self.db_lock.release()

        except redis.exceptions.LockNotOwnedError:
            #TODO
            #logger.warning(f"Cannot release a lock ({self._name})"
            #               f" that's no longer owned ({self.source}) ")
            pass

        except Exception as e:
            #TODO
            #logger.error(f"Could not release lock {self._name} in \
            #             {self.source}. see error: {e}")
            pass

        finally:
            self.send_unlock_cmd()

        return True

    def inspect(self):
        """Returns the current queue and lock holder"""
        holder = self.db_read.get(self.lock_name)
        if holder:
            holder = holder.decode('utf-8')
        queue = self.db_read.zrange(self.queue_name, 0, -1)
        return holder, [elem.decode('utf-8') for elem in queue]

    def extend(self, additional_time: float) -> bool:
        """Adds more time to an already acquired lock."""
        try:
            return self.db_lock.extend(additional_time)

        except redis.exceptions.ConnectionError:
            #TODO
            #logger.warning(f"Could not extend lock ({self._name}). \
            #               Connection error.")
            pass

        except Exception as e:
            #TODO
            #logger.error(f"Could not extend lock {self._name} in \
            #             {self.source}. see error: {e}")
            pass

        return False

    def reacquire(self) -> bool:
        """
        Resets the timeout of an already acquired lock back to a timeout value.
        """
        if not self.should_reacquire:
            return False
        try:
            return self.db_lock.reacquire()

        except redis.exceptions.ConnectionError:
            #TODO
            #logger.warning(f"Could not reacquire lock ({self._name}). \
            #               Connection error.")
            pass

        except redis.exceptions.LockNotOwnedError:
            #TODO
            #logger.warning(f"Could not reacquire lock ({self._name}). \
            #               Lock not owned error.")
            pass

        except Exception as e:
            #TODO
            #logger.error(f"Could not reacquire lock {self._name} in \
            #             {self.source}. see error: {e}")
            pass

        return False

    def is_owned(self):
        """ Returns if the lock is owned."""
        try:
            return self.db_lock.owned()

        except redis.exceptions.ConnectionError:
            #TODO
            #logger.warning(f"Could not check lock ({self._name}) \
            #               ownership. Connection error.")
            pass

        except Exception as e:
            #TODO
            #logger.error(f"Could not check lock ({self._name}) ownership. \
            #             see error:{e}")
            pass

        return False

    def th_reacquire(self):
        """
            Thread to keep Lock heartbeat
            Thread will exit when Lock is not in enabled_locks anymore
        """
        # heartbeat time must be smaller than timeout
        _heartbeat = self.timeout * self.HEARTBEAT_FREQ_FACTOR

        # max retries in case communication fails
        max_retries = self.DEFAULT_MAX_RETRIES

        while True:
            # wait x seconds before reacquire
            asyncio.sleep(_heartbeat)

            # terminate heartbeat
            if self._name not in type(self).enabled_locks \
               or not self.should_reacquire:
                break

            # if cannot reacquire stop doing heartbeat
            if not self.reacquire():
                max_retries -= 1
                if max_retries == 0:
                    type(self).enabled_locks.remove(self._name)
                    #TODO
                    #logger.error(f"Heartbeat could not reacquire lock \
                    #             {self._name} in {self.source}")
                    break
            else:
                max_retries = self.DEFAULT_MAX_RETRIES

    @classmethod
    async def enable_heartbeat(cls, **kwargs):
        """
            Create a thread to continuously keep Lock heartbeat
        """
        # instantiate Lock object
        lock_obj = cls(**kwargs)

        # launch Lock heartbeat if not yet launched
        if lock_obj._name in cls.enabled_locks:
            #TODO
            #logger.debug("Lock already in heartbeat pool")
            pass
        else:
            # append to enabled locks pool
            cls.enabled_locks.append(lock_obj._name)

            # get new loop
            loop = asyncio.get_event_loop()

            # launch thread
            await loop.run_in_executor(None, lock_obj.th_reacquire)

    @classmethod
    def disable_heartbeat(cls, name, **_):
        """
            Disable Lock heartbeat by removing it from enabled_locks
            heartbeat thread will automatically end
        """
        try:
            # remove lock from enabled locks pool
            cls.enabled_locks.remove(name)

        # ignore if the lock is not in enabled_locks
        except ValueError:
            pass

    # pylint: enable=unused-argument

    def send_lock_cmd(self):
        """
            Send spawner a command to enable heartbeat
        """

        # do not heartbeat if timeout less than 1 second
        if self.db_lock.timeout <= self.HEARTBEAT_MIN_TIMEOUT:
            return

        # get instance kwargs
        _kwargs = {
            "name":             self._name,
            "scope":            self.scope,
            "timeout":          self.timeout,
            "queue_level":      self.queue_level,
            "blocking_timeout": self.blocking_timeout,
            "alive_timeout":    self.alive_timeout,
            "_robot_name":      self.robot_name,
            "_node_name":       self.node_name,
            "persistent":       self.persistent,
            "reacquire":        self.should_reacquire
        }

        # send command
        # Robot().send_cmd(command='LOCK', data=_kwargs)

    def send_unlock_cmd(self):
        """
            Send spawner a command to disable heartbeat
        """

        # send command
        # Robot().send_cmd(command='UNLOCK', data={'name': self._name})
