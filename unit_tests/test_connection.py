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


class Test__get_instance(unittest.TestCase):

    def _call_fut(self):
        from google.cloud.happybase.connection import _get_instance
        return _get_instance()

    def _helper(self, instances=(), failed_locations=()):
        from functools import partial

        client_with_instances = partial(
            _Client, instances=instances, failed_locations=failed_locations)

        with mock.patch('google.cloud.happybase.connection.Client',
                        client_with_instances):
            result = self._call_fut()

        # If we've reached this point, then _call_fut didn't fail, so we know
        # there is exactly one instance.
        instance, = instances
        self.assertEqual(result, instance)
        client = instance.client
        self.assertEqual(client.args, ())
        expected_kwargs = {'admin': True}
        self.assertEqual(client.kwargs, expected_kwargs)

    def test_default(self):
        instance = _Instance()
        self._helper(instances=[instance])

    def test_with_no_instances(self):
        with self.assertRaises(ValueError):
            self._helper()

    def test_with_too_many_instances(self):
        instances = [_Instance(), _Instance()]
        with self.assertRaises(ValueError):
            self._helper(instances=instances)

    def test_with_failed_locations(self):
        instance = _Instance()
        failed_location = 'us-central1-c'
        with self.assertRaises(ValueError):
            self._helper(instances=[instance],
                         failed_locations=[failed_location])


class TestConnection(unittest.TestCase):

    def _get_target_class(self):
        from google.cloud.happybase.connection import Connection
        return Connection

    def _make_one(self, *args, **kwargs):
        return self._get_target_class()(*args, **kwargs)

    def test_constructor_defaults(self):
        instance = _Instance()  # Avoid implicit environ check.
        connection = self._make_one(instance=instance)

        self.assertEqual(connection._instance, instance)
        self.assertEqual(connection.table_prefix, None)
        self.assertEqual(connection.table_prefix_separator, '_')

    def test_constructor_no_autoconnect(self):
        instance = _Instance()  # Avoid implicit environ check.
        connection = self._make_one(autoconnect=False, instance=instance)
        self.assertEqual(connection.table_prefix, None)
        self.assertEqual(connection.table_prefix_separator, '_')

    def test_constructor_missing_instance(self):
        instance = _Instance()

        def mock_get_instance():
            return instance

        with mock.patch('google.cloud.happybase.connection._get_instance',
                        mock_get_instance):
            connection = self._make_one(
                autoconnect=False, instance=None)

            self.assertEqual(connection.table_prefix, None)
            self.assertEqual(connection.table_prefix_separator, '_')
            self.assertEqual(connection._instance, instance)

    def test_constructor_explicit(self):
        autoconnect = False
        table_prefix = 'table-prefix'
        table_prefix_separator = 'sep'
        instance = _Instance()

        connection = self._make_one(
            autoconnect=autoconnect,
            table_prefix=table_prefix,
            table_prefix_separator=table_prefix_separator,
            instance=instance)
        self.assertTrue(connection._instance is instance)
        self.assertEqual(connection.table_prefix, table_prefix)
        self.assertEqual(connection.table_prefix_separator,
                         table_prefix_separator)

    def test_constructor_with_unknown_argument(self):
        instance = _Instance()
        with self.assertRaises(TypeError):
            self._make_one(instance=instance, unknown='foo')

    def test_constructor_with_legacy_args(self):
        import warnings

        instance = _Instance()
        with warnings.catch_warnings(record=True) as warned:
            self._make_one(
                instance=instance, host=object(),
                port=object(), compat=object(),
                transport=object(), protocol=object())

        self.assertEqual(len(warned), 1)
        self.assertIn('host', str(warned[0]))
        self.assertIn('port', str(warned[0]))
        self.assertIn('compat', str(warned[0]))
        self.assertIn('transport', str(warned[0]))
        self.assertIn('protocol', str(warned[0]))

    def test_constructor_non_string_prefix(self):
        table_prefix = object()

        with self.assertRaises(TypeError):
            self._make_one(autoconnect=False, table_prefix=table_prefix)

    def test_constructor_non_string_prefix_separator(self):
        table_prefix_separator = object()

        with self.assertRaises(TypeError):
            self._make_one(
                autoconnect=False,
                table_prefix_separator=table_prefix_separator)

    def test__table_name_with_prefix_set(self):
        table_prefix = 'table-prefix'
        table_prefix_separator = '<>'
        instance = _Instance()

        connection = self._make_one(
            autoconnect=False,
            table_prefix=table_prefix,
            table_prefix_separator=table_prefix_separator,
            instance=instance)

        name = 'some-name'
        prefixed = connection._table_name(name)
        self.assertEqual(prefixed,
                         table_prefix + table_prefix_separator + name)

    def test__table_name_with_no_prefix_set(self):
        instance = _Instance()
        connection = self._make_one(autoconnect=False, instance=instance)

        name = 'some-name'
        prefixed = connection._table_name(name)
        self.assertEqual(prefixed, name)

    def test_table_factory(self):
        from google.cloud.happybase.table import Table

        instance = _Instance()  # Avoid implicit environ check.
        connection = self._make_one(autoconnect=False, instance=instance)

        name = 'table-name'
        table = connection.table(name)

        self.assertTrue(isinstance(table, Table))
        self.assertEqual(table.name, name)
        self.assertEqual(table.connection, connection)

    def _table_factory_prefix_helper(self, use_prefix=True):
        from google.cloud.happybase.table import Table

        instance = _Instance()  # Avoid implicit environ check.
        table_prefix = 'table-prefix'
        table_prefix_separator = '<>'
        connection = self._make_one(
            autoconnect=False, table_prefix=table_prefix,
            table_prefix_separator=table_prefix_separator,
            instance=instance)

        name = 'table-name'
        table = connection.table(name, use_prefix=use_prefix)

        self.assertTrue(isinstance(table, Table))
        prefixed_name = table_prefix + table_prefix_separator + name
        if use_prefix:
            self.assertEqual(table.name, prefixed_name)
        else:
            self.assertEqual(table.name, name)
        self.assertEqual(table.connection, connection)

    def test_table_factory_with_prefix(self):
        self._table_factory_prefix_helper(use_prefix=True)

    def test_table_factory_with_ignored_prefix(self):
        self._table_factory_prefix_helper(use_prefix=False)

    def test_tables(self):
        from google.cloud.bigtable.table import Table

        table_name1 = 'table-name1'
        table_name2 = 'table-name2'
        instance = _Instance(list_tables_result=[
            Table(table_name1, None),
            Table(table_name2, None),
        ])
        connection = self._make_one(autoconnect=False, instance=instance)
        result = connection.tables()
        self.assertEqual(result, [table_name1, table_name2])

    def test_tables_with_prefix(self):
        from google.cloud.bigtable.table import Table

        table_prefix = 'prefix'
        table_prefix_separator = '<>'
        unprefixed_table_name1 = 'table-name1'

        table_name1 = (table_prefix + table_prefix_separator +
                       unprefixed_table_name1)
        table_name2 = 'table-name2'
        instance = _Instance(list_tables_result=[
            Table(table_name1, None),
            Table(table_name2, None),
        ])
        connection = self._make_one(
            autoconnect=False, instance=instance, table_prefix=table_prefix,
            table_prefix_separator=table_prefix_separator)
        result = connection.tables()
        self.assertEqual(result, [unprefixed_table_name1])

    def test_create_table(self):
        instance = _Instance()  # Avoid implicit environ check.
        connection = self._make_one(autoconnect=False, instance=instance)
        mock_gc_rule = object()
        called_options = []

        def mock_parse_family_option(option):
            called_options.append(option)
            return mock_gc_rule

        name = 'table-name'
        col_fam1 = 'cf1'
        col_fam_option1 = object()
        col_fam2 = u'cf2'
        col_fam_option2 = object()
        col_fam3 = b'cf3'
        col_fam_option3 = object()
        families = {
            col_fam1: col_fam_option1,
            # A trailing colon is also allowed.
            col_fam2 + ':': col_fam_option2,
            col_fam3 + b':': col_fam_option3,
        }

        tables_created = []

        def make_table(*args, **kwargs):
            result = _MockLowLevelTable(*args, **kwargs)
            tables_created.append(result)
            return result

        patch = mock.patch.multiple(
            'google.cloud.happybase.connection',
            _LowLevelTable=make_table,
            _parse_family_option=mock_parse_family_option,
        )
        with patch:
            connection.create_table(name, families)

        # Just one table would have been created.
        table_instance, = tables_created
        self.assertEqual(table_instance.args, (name, instance))
        self.assertEqual(table_instance.kwargs, {})
        self.assertEqual(table_instance.create_calls, 1)

        # Check if our mock was called twice, but we don't know the order.
        self.assertEqual(
            set(called_options),
            set([col_fam_option1, col_fam_option2, col_fam_option3]))

        col_fam_dict = table_instance.col_fam_dict
        expected_cf_list = ['cf1', 'cf2', 'cf3']
        self.assertEqual(sorted(col_fam_dict), expected_cf_list)

    def test_create_table_bad_type(self):
        instance = _Instance()  # Avoid implicit environ check.
        connection = self._make_one(autoconnect=False, instance=instance)

        name = 'table-name'
        families = None
        with self.assertRaises(TypeError):
            connection.create_table(name, families)

    def test_create_table_bad_value(self):
        instance = _Instance()  # Avoid implicit environ check.
        connection = self._make_one(autoconnect=False, instance=instance)

        name = 'table-name'
        families = {}
        with self.assertRaises(ValueError):
            connection.create_table(name, families)

    def _create_table_error_helper(self, err_val, err_type):
        instance = _Instance()  # Avoid implicit environ check.
        connection = self._make_one(autoconnect=False, instance=instance)

        tables_created = []

        def make_table(*args, **kwargs):
            kwargs['create_error'] = err_val
            result = _MockLowLevelTable(*args, **kwargs)
            tables_created.append(result)
            return result

        name = 'table-name'
        families = {'foo': {}}
        with mock.patch('google.cloud.happybase.connection._LowLevelTable',
                        make_table):
            with self.assertRaises(err_type):
                connection.create_table(name, families)

        self.assertEqual(len(tables_created), 1)
        self.assertEqual(tables_created[0].create_calls, 1)

    def test_create_table_already_exists(self):
        from grpc.beta import interfaces
        from grpc.framework.interfaces.face import face
        from google.cloud.happybase.connection import AlreadyExists

        err_val = face.NetworkError(None, None,
                                    interfaces.StatusCode.ALREADY_EXISTS, None)
        self._create_table_error_helper(err_val, AlreadyExists)

    def test_create_table_connection_error(self):
        from grpc.beta import interfaces
        from grpc.framework.interfaces.face import face
        err_val = face.NetworkError(None, None,
                                    interfaces.StatusCode.INTERNAL, None)
        self._create_table_error_helper(err_val, face.NetworkError)

    def test_create_table_other_error(self):
        self._create_table_error_helper(RuntimeError, RuntimeError)

    def _delete_table_helper(self, disable=False):
        instance = _Instance()  # Avoid implicit environ check.
        connection = self._make_one(autoconnect=False, instance=instance)

        tables_created = []

        def make_table(*args, **kwargs):
            result = _MockLowLevelTable(*args, **kwargs)
            tables_created.append(result)
            return result

        name = 'table-name'
        with mock.patch('google.cloud.happybase.connection._LowLevelTable',
                        make_table):
            connection.delete_table(name, disable=disable)

        # Just one table would have been created.
        table_instance, = tables_created
        self.assertEqual(table_instance.args, (name, instance))
        self.assertEqual(table_instance.kwargs, {})
        self.assertEqual(table_instance.delete_calls, 1)

    def test_delete_table(self):
        self._delete_table_helper()

    def test_delete_table_disable(self):
        import warnings
        from google.cloud.happybase.connection import _DISABLE_DELETE_MSG

        with warnings.catch_warnings(record=True) as warned:
            self._delete_table_helper(disable=True)

        self.assertEqual(len(warned), 1)
        self.assertIn(_DISABLE_DELETE_MSG, str(warned[0]))

    def test_enable_table(self):
        import warnings
        from google.cloud.happybase.connection import _ENABLE_TMPL

        instance = _Instance()  # Avoid implicit environ check.
        connection = self._make_one(autoconnect=False, instance=instance)

        name = 'table-name'

        with warnings.catch_warnings(record=True) as warned:
            connection.enable_table(name)

        self.assertEqual(len(warned), 1)
        self.assertIn(_ENABLE_TMPL % (name,), str(warned[0]))

    def test_disable_table(self):
        import warnings
        from google.cloud.happybase.connection import _DISABLE_TMPL

        instance = _Instance()  # Avoid implicit environ check.
        connection = self._make_one(autoconnect=False, instance=instance)

        name = 'table-name'

        with warnings.catch_warnings(record=True) as warned:
            connection.disable_table(name)

        self.assertEqual(len(warned), 1)
        self.assertIn(_DISABLE_TMPL % (name,), str(warned[0]))

    def test_is_table_enabled(self):
        import warnings
        from google.cloud.happybase.connection import _IS_ENABLED_TMPL

        instance = _Instance()  # Avoid implicit environ check.
        connection = self._make_one(autoconnect=False, instance=instance)

        name = 'table-name'

        with warnings.catch_warnings(record=True) as warned:
            result = connection.is_table_enabled(name)

        self.assertTrue(result)
        self.assertEqual(len(warned), 1)
        self.assertIn(_IS_ENABLED_TMPL % (name,), str(warned[0]))

    def test_compact_table(self):
        import warnings
        from google.cloud.happybase.connection import _COMPACT_TMPL

        instance = _Instance()  # Avoid implicit environ check.
        connection = self._make_one(autoconnect=False, instance=instance)

        name = 'table-name'

        with warnings.catch_warnings(record=True) as warned:
            connection.compact_table(name)

        self.assertEqual(len(warned), 1)
        self.assertIn(_COMPACT_TMPL % (name, False), str(warned[0]))


class Test__parse_family_option(unittest.TestCase):

    def _call_fut(self, option):
        from google.cloud.happybase.connection import _parse_family_option
        return _parse_family_option(option)

    def test_dictionary_no_keys(self):
        option = {}
        result = self._call_fut(option)
        self.assertEqual(result, None)

    def test_null(self):
        option = None
        result = self._call_fut(option)
        self.assertEqual(result, None)

    def test_dictionary_bad_key(self):
        import warnings

        option = {'badkey': None}
        with warnings.catch_warnings(record=True) as warned:
            result = self._call_fut(option)

        self.assertEqual(result, None)
        self.assertEqual(len(warned), 1)
        self.assertIn('badkey', str(warned[0]))

    def test_dictionary_versions_key(self):
        from google.cloud.bigtable.column_family import MaxVersionsGCRule

        versions = 42
        option = {'max_versions': versions}
        result = self._call_fut(option)

        gc_rule = MaxVersionsGCRule(versions)
        self.assertEqual(result, gc_rule)

    def test_dictionary_ttl_key(self):
        import datetime
        from google.cloud.bigtable.column_family import MaxAgeGCRule

        time_to_live = 24 * 60 * 60
        max_age = datetime.timedelta(days=1)
        option = {'time_to_live': time_to_live}
        result = self._call_fut(option)

        gc_rule = MaxAgeGCRule(max_age)
        self.assertEqual(result, gc_rule)

    def test_dictionary_both_keys(self):
        import datetime
        from google.cloud.bigtable.column_family import GCRuleIntersection
        from google.cloud.bigtable.column_family import MaxAgeGCRule
        from google.cloud.bigtable.column_family import MaxVersionsGCRule

        versions = 42
        time_to_live = 24 * 60 * 60
        option = {
            'max_versions': versions,
            'time_to_live': time_to_live,
        }
        result = self._call_fut(option)

        max_age = datetime.timedelta(days=1)
        # NOTE: This relies on the order of the rules in the method we are
        #       calling matching this order here.
        gc_rule1 = MaxAgeGCRule(max_age)
        gc_rule2 = MaxVersionsGCRule(versions)
        gc_rule = GCRuleIntersection(rules=[gc_rule1, gc_rule2])
        self.assertEqual(result, gc_rule)

    def test_non_dictionary(self):
        option = object()
        self.assertFalse(isinstance(option, dict))
        result = self._call_fut(option)
        self.assertEqual(result, option)


class _Client(object):

    def __init__(self, *args, **kwargs):
        self.instances = kwargs.pop('instances', [])
        for instance in self.instances:
            instance.client = self
        self.failed_locations = kwargs.pop('failed_locations', [])
        self.args = args
        self.kwargs = kwargs

    def list_instances(self):
        return self.instances, self.failed_locations


class _Instance(object):

    def __init__(self, list_tables_result=()):
        # Included to support Connection.__del__
        self._client = _Client()
        self.list_tables_result = list_tables_result

    def list_tables(self):
        return self.list_tables_result


class _MockLowLevelTable(object):

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.create_error = kwargs.get('create_error')
        self.delete_calls = 0
        self.create_calls = 0
        self.col_fam_dict = {}

    def delete(self):
        self.delete_calls += 1

    def create(self, column_families):
        self.create_calls += 1
        self.col_fam_dict = column_families
        if self.create_error:
            raise self.create_error
