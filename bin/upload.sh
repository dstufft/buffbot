#!/bin/bash
set -euox pipefail

pyupdater pkg --process --sign
pyupdater upload --service scp
