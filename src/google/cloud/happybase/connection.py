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

"""Google Cloud Bigtable HappyBase connection module."""


import datetime
import warnings

import six

from grpc.beta import interfaces
from grpc.framework.interfaces.face import face

try:
    from happybase.hbase.ttypes import AlreadyExists
except ImportError:
    from google.cloud.exceptions import Conflict as AlreadyExists

from google.cloud.bigtable.client import Client
from google.cloud.bigtable.column_family import GCRuleIntersection
from google.cloud.bigtable.column_family import MaxAgeGCRule
from google.cloud.bigtable.column_family import MaxVersionsGCRule
from google.cloud.bigtable.table import Table as _LowLevelTable

from google.cloud.happybase.table import Table

# Constants reproduced here for HappyBase compatibility, though values
# are all null.
COMPAT_MODES = None
THRIFT_TRANSPORTS = None
THRIFT_PROTOCOLS = None
DEFAULT_HOST = None
DEFAULT_PORT = None
DEFAULT_TRANSPORT = None
DEFAULT_COMPAT = None
DEFAULT_PROTOCOL = None

_LEGACY_ARGS = frozenset(("host", "port", "compat", "transport", "protocol"))
_BASE_DISABLE = "Cloud Bigtable has no concept of enabled / disabled tables."
_DISABLE_DELETE_MSG = (
    "The disable argument should not be used in " "delete_table(). "
) + _BASE_DISABLE
_ENABLE_TMPL = "Connection.enable_table(%r) was called, but " + _BASE_DISABLE
_DISABLE_TMPL = "Connection.disable_table(%r) was called, but " + _BASE_DISABLE
_IS_ENABLED_TMPL = "Connection.is_table_enabled(%r) was called, but " + _BASE_DISABLE
_COMPACT_TMPL = (
    "Connection.compact_table(%r, major=%r) was called, but the "
    "Cloud Bigtable API handles table compactions automatically "
    "and does not expose an API for it."
)


def _get_instance():
    """Gets instance for the default project.

    Creates a client with the inferred credentials and project ID from
    the local environment. Then uses
    :meth:`.bigtable.client.Client.list_instances` to
    get the unique instance owned by the project.

    If the request fails for any reason, or if there isn't exactly one instance
    owned by the project, then this function will fail.

    :rtype: :class:`~google.cloud.bigtable.instance.Instance`
    :returns: The unique instance owned by the project inferred from
              the environment.
    :raises ValueError: if there is a failed location or any number of
                        instances other than one.
    """
    client_kwargs = {"admin": True}
    client = Client(**client_kwargs)
    instances, failed_locations = client.list_instances()

    if failed_locations:
        raise ValueError(
            "Determining instance via ListInstances encountered " "failed locations."
        )
    num_instances = len(instances)
    if num_instances == 0:
        raise ValueError("This client doesn't have access to any instances.")
    if num_instances > 1:
        raise ValueError(
            "This client has access to more than one instance. "
            "Please directly pass the instance you'd "
            "like to use."
        )
    return instances[0]


class Connection(object):
    """Connection to Cloud Bigtable backend.

    The arguments ``host``, ``port``, ``compat``, ``transport`` and
    ``protocol`` are allowed (as keyword arguments) for compatibility with
    HappyBase. However, they will not be used in any way, and will cause a
    warning if passed.

    :type autoconnect: bool
    :param autoconnect: (Optional) Whether the connection should be
                        :meth:`open`-ed during construction.

    :type table_prefix: str
    :param table_prefix: (Optional) Prefix used to construct table names.

    :type table_prefix_separator: str
    :param table_prefix_separator: (Optional) Separator used with
                                   ``table_prefix``. Defaults to ``_``.

    :type instance: :class:`~google.cloud.bigtable.instance.Instance`
    :param instance: (Optional) A Cloud Bigtable instance. The instance also
                    owns a client for making gRPC requests to the Cloud
                    Bigtable API. If not passed in, defaults to creating client
                    with ``admin=True`` and using the ``timeout`` here for the
                    ``timeout_seconds`` argument to the
                    :class:`~google.cloud.bigtable.client.Client`
                    constructor. The credentials for the client
                    will be the implicit ones loaded from the environment.
                    Then that client is used to retrieve all the instances
                    owned by the client's project.

    :type kwargs: dict
    :param kwargs: Remaining keyword arguments. Provided for HappyBase
                   compatibility.
    """

    _instance = None

    def __init__(
        self,
        autoconnect=True,
        table_prefix=None,
        table_prefix_separator="_",
        instance=None,
        **kwargs
    ):
        self._handle_legacy_args(kwargs)
        if table_prefix is not None:
            if not isinstance(table_prefix, six.string_types):
                raise TypeError(
                    "table_prefix must be a string",
                    "received",
                    table_prefix,
                    type(table_prefix),
                )

        if not isinstance(table_prefix_separator, six.string_types):
            raise TypeError(
                "table_prefix_separator must be a string",
                "received",
                table_prefix_separator,
                type(table_prefix_separator),
            )

        self.table_prefix = table_prefix
        self.table_prefix_separator = table_prefix_separator

        if instance is None:
            instance = _get_instance()
        self._instance = instance

        if autoconnect:
            self.open()

        self._initialized = True

    @staticmethod
    def _handle_legacy_args(arguments_dict):
        """Check legacy HappyBase arguments and warn if set.

        :type arguments_dict: dict
        :param arguments_dict: Unused keyword arguments.

        :raises TypeError: if a keyword other than ``host``, ``port``,
                           ``compat``, ``transport`` or ``protocol`` is used.
        """
        common_args = _LEGACY_ARGS.intersection(six.iterkeys(arguments_dict))
        if common_args:
            all_args = ", ".join(common_args)
            message = (
                "The HappyBase legacy arguments %s were used. These "
                "arguments are unused by google-cloud." % (all_args,)
            )
            warnings.warn(message)
        for arg_name in common_args:
            arguments_dict.pop(arg_name)
        if arguments_dict:
            unexpected_names = arguments_dict.keys()
            raise TypeError("Received unexpected arguments", unexpected_names)

    def open(self):
        """Open the underlying transport to Cloud Bigtable.

        This method does nothing and is provided for compatibility.
        """

    def close(self):
        """Close the underlying transport to Cloud Bigtable.

        This method does nothing and is provided for compatibility.
        """

    def _table_name(self, name):
        """Construct a table name by optionally adding a table name prefix.

        :type name: str
        :param name: The name to have a prefix added to it.

        :rtype: str
        :returns: The prefixed name, if the current connection has a table
                  prefix set.
        """
        if self.table_prefix is None:
            return name

        return self.table_prefix + self.table_prefix_separator + name

    def table(self, name, use_prefix=True):
        """Table factory.

        :type name: str
        :param name: The name of the table to be created.

        :type use_prefix: bool
        :param use_prefix: Whether to use the table prefix (if any).

        :rtype: :class:`Table <google.cloud.happybase.table.Table>`
        :returns: Table instance owned by this connection.
        """
        if use_prefix:
            name = self._table_name(name)
        return Table(name, self)

    def tables(self):
        """Return a list of table names available to this connection.

        .. note::

            This lists every table in the instance owned by this connection,
            **not** every table that a given user may have access to.

        .. note::

            If ``table_prefix`` is set on this connection, only returns the
            table names which match that prefix.

        :rtype: list
        :returns: List of string table names.
        """
        low_level_table_instances = self._instance.list_tables()
        table_names = [
            table_instance.table_id for table_instance in low_level_table_instances
        ]

        # Filter using prefix, and strip prefix from names
        if self.table_prefix is not None:
            prefix = self._table_name("")
            offset = len(prefix)
            table_names = [
                name[offset:] for name in table_names if name.startswith(prefix)
            ]

        return table_names

    def create_table(self, name, families):
        """Create a table.

        .. warning::

            The only column family options from HappyBase that are able to be
            used with Cloud Bigtable are ``max_versions`` and ``time_to_live``.

        Values in ``families`` represent column family options. In HappyBase,
        these are dictionaries, corresponding to the ``ColumnDescriptor``
        structure in the Thrift API. The accepted keys are:

        * ``max_versions`` (``int``)
        * ``compression`` (``str``)
        * ``in_memory`` (``bool``)
        * ``bloom_filter_type`` (``str``)
        * ``bloom_filter_vector_size`` (``int``)
        * ``bloom_filter_nb_hashes`` (``int``)
        * ``block_cache_enabled`` (``bool``)
        * ``time_to_live`` (``int``)

        :type name: str
        :param name: The name of the table to be created.

        :type families: dict
        :param families: Dictionary with column family names as keys and column
                         family options as the values. The options can be among

                         * :class:`dict`
                         * :class:`.GarbageCollectionRule`

        :raises TypeError: If ``families`` is not a dictionary.
        :raises ValueError: If ``families`` has no entries.
        :raises AlreadyExists: If creation fails due to an already
                               existing table.
        :raises NetworkError: If creation fails for a reason other than
                              table exists.
        """
        if not isinstance(families, dict):
            raise TypeError("families arg must be a dictionary")

        if not families:
            raise ValueError(
                "Cannot create table %r (no column " "families specified)" % (name,)
            )

        # Parse all keys before making any API requests.
        gc_rule_dict = {}
        for column_family_name, option in families.items():
            if isinstance(column_family_name, six.binary_type):
                column_family_name = column_family_name.decode("utf-8")
            if column_family_name.endswith(":"):
                column_family_name = column_family_name[:-1]
            gc_rule_dict[column_family_name] = _parse_family_option(option)

        # Create table instance and then make API calls.
        name = self._table_name(name)
        low_level_table = _LowLevelTable(name, self._instance)

        try:
            low_level_table.create(column_families=gc_rule_dict)
        except face.NetworkError as network_err:
            if network_err.code == interfaces.StatusCode.ALREADY_EXISTS:
                raise AlreadyExists(name)
            else:
                raise

    def delete_table(self, name, disable=False):
        """Delete the specified table.

        :type name: str
        :param name: The name of the table to be deleted. If ``table_prefix``
                     is set, a prefix will be added to the ``name``.

        :type disable: bool
        :param disable: Whether to first disable the table if needed. This
                        is provided for compatibility with HappyBase, but is
                        not relevant for Cloud Bigtable since it has no concept
                        of enabled / disabled tables.
        """
        if disable:
            warnings.warn(_DISABLE_DELETE_MSG)

        name = self._table_name(name)
        _LowLevelTable(name, self._instance).delete()

    @staticmethod
    def enable_table(name):
        """Enable the specified table.

        .. warning::

            Cloud Bigtable has no concept of enabled / disabled tables so this
            method does nothing. It is provided simply for compatibility.

        :type name: str
        :param name: The name of the table to be enabled.
        """
        warnings.warn(_ENABLE_TMPL % (name,))

    @staticmethod
    def disable_table(name):
        """Disable the specified table.

        .. warning::

            Cloud Bigtable has no concept of enabled / disabled tables so this
            method does nothing. It is provided simply for compatibility.

        :type name: str
        :param name: The name of the table to be disabled.
        """
        warnings.warn(_DISABLE_TMPL % (name,))

    @staticmethod
    def is_table_enabled(name):
        """Return whether the specified table is enabled.

        .. warning::

            Cloud Bigtable has no concept of enabled / disabled tables so this
            method always returns :data:`True`. It is provided simply for
            compatibility.

        :type name: str
        :param name: The name of the table to check enabled / disabled status.

        :rtype: bool
        :returns: The value :data:`True` always.
        """
        warnings.warn(_IS_ENABLED_TMPL % (name,))
        return True

    @staticmethod
    def compact_table(name, major=False):
        """Compact the specified table.

        .. warning::

            Cloud Bigtable supports table compactions, it just doesn't expose
            an API for that feature, so this method does nothing. It is
            provided simply for compatibility.

        :type name: str
        :param name: The name of the table to compact.

        :type major: bool
        :param major: Whether to perform a major compaction.
        """
        warnings.warn(_COMPACT_TMPL % (name, major))


def _parse_family_option(option):
    """Parses a column family option into a garbage collection rule.

    .. note::

        If ``option`` is not a dictionary, the type is not checked.
        If ``option`` is :data:`None`, there is nothing to do, since this
        is the correct output.

    :type option: :class:`dict`,
                  :data:`NoneType <types.NoneType>`,
                  :class:`.GarbageCollectionRule`
    :param option: A column family option passes as a dictionary value in
                   :meth:`Connection.create_table`.

    :rtype: :class:`.GarbageCollectionRule`
    :returns: A garbage collection rule parsed from the input.
    """
    result = option
    if isinstance(result, dict):
        if not set(result.keys()) <= set(["max_versions", "time_to_live"]):
            all_keys = ", ".join(repr(key) for key in result.keys())
            warning_msg = (
                "Cloud Bigtable only supports max_versions and "
                "time_to_live column family settings. "
                "Received: %s" % (all_keys,)
            )
            warnings.warn(warning_msg)

        max_num_versions = result.get("max_versions")
        max_age = None
        if "time_to_live" in result:
            max_age = datetime.timedelta(seconds=result["time_to_live"])

        versions_rule = age_rule = None
        if max_num_versions is not None:
            versions_rule = MaxVersionsGCRule(max_num_versions)
        if max_age is not None:
            age_rule = MaxAgeGCRule(max_age)

        if versions_rule is None:
            result = age_rule
        else:
            if age_rule is None:
                result = versions_rule
            else:
                result = GCRuleIntersection(rules=[age_rule, versions_rule])

    return result
