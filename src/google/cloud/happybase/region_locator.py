# Copyright 2019 Google Inc.
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

"""Google Cloud Bigtable HappyBase table module."""


class RegionLocation(object):
    """Representation of region of Bigtable

    :type start_key = bytes
    :param start_key = starting key of region is inclusive

    :type end_key : bytes
    :param end_key : ending key of region is exclusive

    """

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return other.start_key == self.start_key and self.end_key == other.end_key

    def __ne__(self, other):
        return not self == other

    def __init__(self, start_key=b"", end_key=b""):
        self.start_key = start_key
        self.end_key = end_key
