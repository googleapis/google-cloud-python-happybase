# Copyright 2014 Google Inc.
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

from __future__ import print_function
import os
import sys
import time

from google.auth.environment_vars import CREDENTIALS as TEST_CREDENTIALS


# From shell environ. May be None.
CREDENTIALS = os.getenv(TEST_CREDENTIALS)

ENVIRON_ERROR_MSG = """\
To run the system tests, you need to set some environment variables.
Please check the CONTRIBUTING guide for instructions.
"""


class EmulatorCreds(object):
    """A mock credential object.

    Used to avoid unnecessary token refreshing or reliance on the network
    while an emulator is running.
    """

    @staticmethod
    def create_scoped_required():
        return False


def check_environ():
    err_msg = None
    if CREDENTIALS is None:
        err_msg = "\nMissing variables: " + TEST_CREDENTIALS
    elif not os.path.isfile(CREDENTIALS):
        err_msg = "\nThe %s path %r is not a file." % (TEST_CREDENTIALS, CREDENTIALS)

    if err_msg is not None:
        msg = ENVIRON_ERROR_MSG + err_msg
        print(msg, file=sys.stderr)
        sys.exit(1)


def unique_resource_id(delimiter="_"):
    """A unique identifier for a resource.

    Intended to help locate resources created in particular
    testing environments and at particular times.
    """
    build_id = os.getenv("TRAVIS_BUILD_ID", "")
    if build_id == "":
        return "%s%d" % (delimiter, 1000 * time.time())

    return "%s%s%s%d" % (delimiter, build_id, delimiter, time.time())
