# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

from PyQt5.QtWidgets import QApplication

from buffbot.ui import MainWindow

APP_NAME = "BuffBot"
APP_VERSION = "0.4.2"

if __name__ == "__main__":
    app = QApplication([])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    window = MainWindow(APP_NAME, APP_VERSION)
    window.show()

    sys.exit(app.exec_())
