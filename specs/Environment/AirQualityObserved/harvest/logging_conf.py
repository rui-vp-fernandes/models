#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# Copyright 2019 FIWARE Foundation, e.V.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
##
from os.path import exists, join, dirname, abspath
from os import mkdir
from logging import getLogger, Formatter, StreamHandler, ERROR, INFO
from logging.handlers import RotatingFileHandler
from sys import stdout

__author__ = 'Fernando López'


class LoggingConf:
    def __init__(self, loglevel=INFO, log_file='log_file.log'):
        codehome = dirname(abspath(__file__))
        loghome = join(codehome, 'logs')

        if exists(loghome) is False:
            mkdir(loghome)

        log_filename = join(loghome, log_file)
        format_str = '%(asctime)s [%(levelname)s] %(module)s: %(message)s'
        date_format = '%Y-%m-%dT%H:%M:%SZ'

        self.sp_logger = getLogger()
        self.sp_logger.setLevel(loglevel)
        formatter = Formatter(fmt=format_str, datefmt=date_format)

        #  Add the log message handler to the logger
        fh = RotatingFileHandler(filename=log_filename, maxBytes=2000000, backupCount=3)
        fh.setLevel(loglevel)
        fh.setFormatter(formatter)
        self.sp_logger.addHandler(fh)

        sh = StreamHandler(stdout)
        sh.setLevel(ERROR)
        sh.setFormatter(formatter)
        self.sp_logger.addHandler(sh)

    def close(self):
        self.sp_logger.handlers.clear()
