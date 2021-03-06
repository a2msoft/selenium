# Licensed to the Software Freedom Conservancy (SFC) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The SFC licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import os
import errno
import subprocess
from subprocess import PIPE
import time

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common import utils

class Service(object):
    """
    Object that manages the starting and stopping of the ChromeDriver
    """

    def __init__(self, executable_path, port=0, service_args=None,
                 log_path=None, env=None):
        """
        Creates a new instance of the Service

        :Args:
         - executable_path : Path to the ChromeDriver
         - port : Port the service is running on
         - service_args : List of args to pass to the chromedriver service
         - log_path : Path for the chromedriver service to log to"""

        self.port = port
        self.path = executable_path
        self.service_args = service_args or []
        if log_path:
          self.service_args.append('--log-path=%s' % log_path)
        if self.port == 0:
            self.port = utils.free_port()
        self.env = env

    def start(self):
        """
        Starts the ChromeDriver Service.

        :Exceptions:
         - WebDriverException : Raised either when it cannot find the
           executable, when it does not have permissions for the
           executable, or when it cannot connect to the service.
         - Possibly other Exceptions in rare circumstances (OSError, etc).
        """
        env = self.env or os.environ
        try:
            self.process = subprocess.Popen([
              self.path,
              "--port=%d" % self.port] +
              self.service_args, env=env, stdout=PIPE, stderr=PIPE)
        except OSError as err:
            docs_msg = "Please see " \
                   "https://sites.google.com/a/chromium.org/chromedriver/home"
            if err.errno == errno.ENOENT:
                raise WebDriverException(
                    "'%s' executable needs to be in PATH. %s" % (
                        os.path.basename(self.path), docs_msg)
                )
            elif err.errno == errno.EACCES:
                raise WebDriverException(
                    "'%s' executable may have wrong permissions. %s" % (
                        os.path.basename(self.path), docs_msg)
                )
            else:
                raise
        count = 0
        while not utils.is_connectable(self.port):
            count += 1
            time.sleep(1)
            if count == 30:
                raise WebDriverException("Can not connect to the '" +
                                         os.path.basename(self.path) + "'")

    @property
    def service_url(self):
        """
        Gets the url of the ChromeDriver Service
        """
        return "http://localhost:%d" % self.port

    def stop(self):
        """
        Tells the ChromeDriver to stop and cleans up the process
        """
        #If its dead dont worry
        if self.process is None:
            return

        #Tell the Server to die!
        try:
            from urllib import request as url_request
        except ImportError:
            import urllib2 as url_request

        url_request.urlopen("http://127.0.0.1:%d/shutdown" % self.port)
        count = 0
        while utils.is_connectable(self.port):
            if count == 30:
               break
            count += 1
            time.sleep(1)

        #Tell the Server to properly die in case
        try:
            if self.process:
                self.process.stdout.close()
                self.process.stderr.close()
                self.process.kill()
                self.process.wait()
        except OSError:
            # kill may not be available under windows environment
            pass
