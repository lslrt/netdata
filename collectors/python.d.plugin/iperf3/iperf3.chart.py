# -*- coding: utf-8 -*-
# Description: Parse iperf3 server log
# Author: Leo Sartre
# SPDX-License-Identifier: GPL-3.0-or-later

from bases.FrameworkServices.LogService import LogService

import re

NETDATA_UPDATE_EVERY=1
priority = 90000

ORDER = [
    "Bandwidth"
]

CHARTS = {
    "Bandwidth": {
        "options": [None, "Bandwidth", "bits/sec", "IPERF", "iperf3.bandwith", "line"],
        "lines": [
            # lines are created dynamically in `check()`
        ]
    }
}

RE_PORT = re.compile(r'Server listening on (\d+)')
RE_BDWTH = re.compile(r'(\d+\.?\d*)-(\d+\.?\d*).*?(\d+\.?\d*) ([KMG]?bits)/sec')

class Service(LogService):
    def __init__(self, configuration=None, name=None):
        LogService.__init__(self, configuration=configuration, name=name)
        self.order = ORDER
        self.definitions = CHARTS
        self.log_path = self.configuration.get('path', "/tmp/iperfs.log")
        self.line_name = None
        self.bdwth_data = []

    def get_iperf_port_no(self):
        lines = self._get_raw_data()
        if not lines:
            return None

        for l in reversed(lines):
            port = RE_PORT.findall(l)
            if port:
                break # stops as soon as the port is found

        if port:
            return port[0]

        return None

    def check(self):
        """
        Get the port number on which the server listen and create the line
        """
        if not LogService.check(self):
            return False

        self.line_name = self.get_iperf_port_no()
        if not self.line_name:
            return False

        self.definitions['Bandwidth']['lines'].append([self.line_name])

        return True

    def get_data(self):
        # parse new lines and append data to the bdwth_data list
        lines = self._get_raw_data()
        for l in lines:
            tuple = RE_BDWTH.findall(l)
            v = 0
            if tuple:
                start, stop, value, unit = tuple[0]
                # ignore last iperf line that is garbage
                if start == stop:
                    break
                v = float(value)
                if unit == "bits":
                    v *= 1
                elif unit == 'Kbits':
                    v *= 1000
                elif unit == 'Mbits':
                    v *= 1000000
                elif unit == 'Gbits':
                    v *= 1000000000
                else:
                    self.warning("Unexpected unit found: {}!".format(unit))
                    continue
            self.bdwth_data.append(int(v))
            self.info("{} added to the queue".format(int(v)))

        # dequeue the bdwth_data list
        if self.bdwth_data:
            value = self.bdwth_data.pop(0)
            self.info("Returning {}".format(value))
            return {self.line_name: value}
        else:
            return {self.line_name: 0}
