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

import mock


class TestConnectionPool(unittest.TestCase):

    def _get_target_class(self):
        from google.cloud.happybase.pool import ConnectionPool
        return ConnectionPool

    def _make_one(self, *args, **kwargs):
        return self._get_target_class()(*args, **kwargs)

    def test_constructor_defaults(self):
        import six
        import threading
        from google.cloud.happybase.connection import Connection

        size = 11
        instance = _Instance()  # Avoid implicit environ check.
        pool = self._make_one(size, instance=instance)

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
        pool = self._make_one(
            size,
            table_prefix=table_prefix,
            table_prefix_separator=table_prefix_separator,
            instance=instance)

        for connection in pool._queue.queue:
            self.assertEqual(connection.table_prefix, table_prefix)
            self.assertEqual(connection.table_prefix_separator,
                             table_prefix_separator)

    def test_constructor_ignores_autoconnect(self):
        from google.cloud.happybase.connection import Connection

        class ConnectionWithOpen(Connection):

            _open_called = False

            def open(self):
                self._open_called = True

        # First make sure the custom Connection class does as expected.
        instance = _Instance()
        connection = ConnectionWithOpen(autoconnect=False, instance=instance)
        self.assertTrue(connection._instance is instance)
        self.assertFalse(connection._open_called)
        connection = ConnectionWithOpen(autoconnect=True, instance=instance)
        self.assertTrue(connection._open_called)

        # Then make sure autoconnect=True is ignored in a pool.
        size = 1
        with mock.patch('google.cloud.happybase.pool.Connection',
                        ConnectionWithOpen):
            pool = self._make_one(size, autoconnect=True, instance=instance)

        for connection in pool._queue.queue:
            self.assertTrue(isinstance(connection, ConnectionWithOpen))
            self.assertFalse(connection._open_called)

    def test_constructor_infers_instance(self):
        from google.cloud.happybase.connection import Connection

        size = 1
        instance = _Instance()
        get_instance_calls = []

        def mock_get_instance(timeout=None):
            get_instance_calls.append(timeout)
            return instance

        with mock.patch('google.cloud.happybase.pool._get_instance',
                        mock_get_instance):
            pool = self._make_one(size)

        for connection in pool._queue.queue:
            self.assertTrue(isinstance(connection, Connection))
            self.assertTrue(connection._instance is instance)

        self.assertEqual(get_instance_calls, [None])

    def test_constructor_non_integer_size(self):
        size = None
        with self.assertRaises(TypeError):
            self._make_one(size)

    def test_constructor_non_positive_size(self):
        size = -10
        with self.assertRaises(ValueError):
            self._make_one(size)
        size = 0
        with self.assertRaises(ValueError):
            self._make_one(size)

    def _make_one_with_mock_queue(self, queue_return):
        # We are going to use a fake queue, so we don't want any connections
        # or instances to be created in the constructor.
        size = -1
        instance = object()
        with mock.patch('google.cloud.happybase.pool._MIN_POOL_SIZE', size):
            pool = self._make_one(size, instance=instance)

        pool._queue = _Queue(queue_return)
        return pool

    def test__acquire_connection(self):
        queue_return = object()
        pool = self._make_one_with_mock_queue(queue_return)

        timeout = 432
        connection = pool._acquire_connection(timeout=timeout)
        self.assertTrue(connection is queue_return)
        self.assertEqual(pool._queue._get_calls, [(True, timeout)])
        self.assertEqual(pool._queue._put_calls, [])

    def test__acquire_connection_failure(self):
        from google.cloud.happybase.pool import NoConnectionsAvailable

        pool = self._make_one_with_mock_queue(None)
        timeout = 1027
        with self.assertRaises(NoConnectionsAvailable):
            pool._acquire_connection(timeout=timeout)
        self.assertEqual(pool._queue._get_calls, [(True, timeout)])
        self.assertEqual(pool._queue._put_calls, [])

    def test_connection_is_context_manager(self):
        import contextlib
        import six

        queue_return = _Connection()
        pool = self._make_one_with_mock_queue(queue_return)
        cnxn_context = pool.connection()
        if six.PY3:  # pragma: NO COVER Python 3
            self.assertTrue(isinstance(cnxn_context,
                                       contextlib._GeneratorContextManager))
        else:
            self.assertTrue(isinstance(cnxn_context,
                                       contextlib.GeneratorContextManager))

    def test_connection_no_current_cnxn(self):
        queue_return = _Connection()
        pool = self._make_one_with_mock_queue(queue_return)
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
        pool = self._make_one_with_mock_queue(queue_return)
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

    def __init__(self):
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
