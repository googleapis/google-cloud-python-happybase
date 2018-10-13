# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest


class TestConnectionPool(unittest.TestCase):

    def _getTargetClass(self):
        from google.cloud.happybase.pool import ConnectionPool
        return ConnectionPool

    def _makeOne(self, *args, **kwargs):
        return self._getTargetClass()(*args, **kwargs)

    def test_constructor_defaults(self):
        import six
        import threading
        from google.cloud.happybase.connection import Connection

        size = 11
        instance_copy = _Instance()
        all_copies = [instance_copy] * size
        instance = _Instance(all_copies)  # Avoid implicit environ check.
        pool = self._makeOne(size, instance=instance)

        self.assertTrue(isinstance(pool._lock, type(threading.Lock())))
        self.assertTrue(isinstance(pool._thread_connections, threading.local))
        self.assertEqual(pool._thread_connections.__dict__, {})

        queue = pool._queue
        self.assertTrue(isinstance(queue, six.moves.queue.LifoQueue))
        self.assertTrue(queue.full())
        self.assertEqual(queue.maxsize, size)
        for connection in queue.queue:
            self.assertTrue(isinstance(connection, Connection))

    def test_constructor_passes_kwargs(self):
        table_prefix = 'foo'
        table_prefix_separator = '<>'
        instance = _Instance()  # Avoid implicit environ check.

        size = 1
        pool = self._makeOne(size, table_prefix=table_prefix,
                             table_prefix_separator=table_prefix_separator,
                             instance=instance)

        for connection in pool._queue.queue:
            self.assertEqual(connection.table_prefix, table_prefix)
            self.assertEqual(connection.table_prefix_separator,
                             table_prefix_separator)

    def test_constructor_ignores_autoconnect(self):
        from google.cloud._testing import _Monkey
        from google.cloud.happybase.connection import Connection
        from google.cloud.happybase import pool as MUT

        class ConnectionWithOpen(Connection):

            _open_called = False

            def open(self):
                self._open_called = True

        # First make sure the custom Connection class does as expected.
        instance_copy1 = _Instance()
        instance_copy2 = _Instance()
        instance_copy3 = _Instance()
        instance = _Instance([instance_copy1, instance_copy2, instance_copy3])
        connection = ConnectionWithOpen(autoconnect=False, instance=instance)
        self.assertFalse(connection._open_called)
        connection = ConnectionWithOpen(autoconnect=True, instance=instance)
        self.assertTrue(connection._open_called)

        # Then make sure autoconnect=True is ignored in a pool.
        size = 1
        with _Monkey(MUT, Connection=ConnectionWithOpen):
            pool = self._makeOne(size, autoconnect=True, instance=instance)

        for connection in pool._queue.queue:
            self.assertTrue(isinstance(connection, ConnectionWithOpen))
            self.assertFalse(connection._open_called)

    def test_constructor_infers_instance(self):
        from google.cloud._testing import _Monkey
        from google.cloud.happybase.connection import Connection
        from google.cloud.happybase import pool as MUT

        size = 1
        instance_copy = _Instance()
        all_copies = [instance_copy] * size
        instance = _Instance(all_copies)
        get_instance_calls = []

        def mock_get_instance(timeout=None):
            get_instance_calls.append(timeout)
            return instance

        with _Monkey(MUT, _get_instance=mock_get_instance):
            pool = self._makeOne(size)

        for connection in pool._queue.queue:
            self.assertTrue(isinstance(connection, Connection))

        self.assertEqual(get_instance_calls, [None])

    def test_constructor_non_integer_size(self):
        size = None
        with self.assertRaises(TypeError):
            self._makeOne(size)

    def test_constructor_non_positive_size(self):
        size = -10
        with self.assertRaises(ValueError):
            self._makeOne(size)
        size = 0
        with self.assertRaises(ValueError):
            self._makeOne(size)

    def _makeOneWithMockQueue(self, queue_return):
        from google.cloud._testing import _Monkey
        from google.cloud.happybase import pool as MUT

        # We are going to use a fake queue, so we don't want any connections
        # or instances to be created in the constructor.
        size = -1
        instance = object()
        with _Monkey(MUT, _MIN_POOL_SIZE=size):
            pool = self._makeOne(size, instance=instance)

        pool._queue = _Queue(queue_return)
        return pool

    def test__acquire_connection(self):
        queue_return = object()
        pool = self._makeOneWithMockQueue(queue_return)

        timeout = 432
        connection = pool._acquire_connection(timeout=timeout)
        self.assertTrue(connection is queue_return)
        self.assertEqual(pool._queue._get_calls, [(True, timeout)])
        self.assertEqual(pool._queue._put_calls, [])

    def test__acquire_connection_failure(self):
        from google.cloud.happybase.pool import NoConnectionsAvailable

        pool = self._makeOneWithMockQueue(None)
        timeout = 1027
        with self.assertRaises(NoConnectionsAvailable):
            pool._acquire_connection(timeout=timeout)
        self.assertEqual(pool._queue._get_calls, [(True, timeout)])
        self.assertEqual(pool._queue._put_calls, [])

    def test_connection_is_context_manager(self):
        import contextlib
        import six

        queue_return = _Connection()
        pool = self._makeOneWithMockQueue(queue_return)
        cnxn_context = pool.connection()
        if six.PY3:  # pragma: NO COVER Python 3
            self.assertTrue(isinstance(cnxn_context,
                                       contextlib._GeneratorContextManager))
        else:
            self.assertTrue(isinstance(cnxn_context,
                                       contextlib.GeneratorContextManager))

    def test_connection_no_current_cnxn(self):
        queue_return = _Connection()
        pool = self._makeOneWithMockQueue(queue_return)
        timeout = 55

        self.assertFalse(hasattr(pool._thread_connections, 'current'))
        with pool.connection(timeout=timeout) as connection:
            self.assertEqual(pool._thread_connections.current, queue_return)
            self.assertTrue(connection is queue_return)
        self.assertFalse(hasattr(pool._thread_connections, 'current'))

        self.assertEqual(pool._queue._get_calls, [(True, timeout)])
        self.assertEqual(pool._queue._put_calls,
                         [(queue_return, None, None)])

    def test_connection_with_current_cnxn(self):
        current_cnxn = _Connection()
        queue_return = _Connection()
        pool = self._makeOneWithMockQueue(queue_return)
        pool._thread_connections.current = current_cnxn
        timeout = 8001

        with pool.connection(timeout=timeout) as connection:
            self.assertTrue(connection is current_cnxn)

        self.assertEqual(pool._queue._get_calls, [])
        self.assertEqual(pool._queue._put_calls, [])
        self.assertEqual(pool._thread_connections.current, current_cnxn)


class _Client(object):
    pass


class _Connection(object):

    def open(self):
        pass


class _Instance(object):

    def __init__(self, copies=()):
        self.copies = list(copies)
        # Included to support Connection.__del__
        self._client = _Client()


class _Queue(object):

    def __init__(self, result=None):
        self.result = result
        self._get_calls = []
        self._put_calls = []

    def get(self, block=None, timeout=None):
        self._get_calls.append((block, timeout))
        if self.result is None:
            import six
            raise six.moves.queue.Empty
        else:
            return self.result

    def put(self, item, block=None, timeout=None):
        self._put_calls.append((item, block, timeout))
