#!/usr/bin/env python
# -*- encoding: utf-8 -*-
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

from argparse import ArgumentParser
from csv import reader
from datetime import datetime, timedelta
from urllib.request import urlopen
from urllib.error import HTTPError
from io import StringIO
from logging import getLogger, Formatter, DEBUG
from logging.handlers import RotatingFileHandler
from re import sub
from pytz import timezone
from contextlib import closing
from ssl import create_default_context
from certifi import where
from requests import post
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from time import sleep


class AirQualityObserved:
    def __init__(self, stations,
                 fiware_service='AirQuality',
                 fiware_service_path='/Spain_Madrid',
                 endpoint='http://localhost:1030',
                 only_latest=False,
                 logger=None):

        if logger is not None:
            self.logger = logger

        self.logger.debug('#### Starting a new harvesting and harmonization cycle ... ####')

        # Entity type
        self.AMBIENT_TYPE_NAME = 'AirQualityObserved'

        # Orion service that will store the data
        self.orion_service = endpoint

        self.only_latest = only_latest

        self.stations_to_retrieve_data = []

        self.madrid_tz = timezone('CET')

        self.pollutant_dict = {
            '01': 'SO2',
            '06': 'CO',
            '07': 'NO',
            '08': 'NO2',
            '09': 'PM2.5',
            '10': 'PM10',
            '12': 'NOx',
            '14': 'O3',
            '20': 'TOL',
            '30': 'BEN',
            '35': 'EBE',
            '37': 'MXY',
            '38': 'PXY',
            '39': 'OXY',
            '42': 'TCH',
            '43': 'CH4',
            '44': 'NHMC'
        }

        self.pollutant_descriptions = {
            '01': 'Sulfur Dioxide',
            '06': 'Carbon Monoxide',
            '07': 'Nitrogen Monoxide',
            '08': 'Nitrogen Dioxide',
            '09': 'Particles lower than 2.5',
            '10': 'Particles lower than 10',
            '12': 'Nitrogen oxides',
            '14': 'Ozone',
            '20': 'Toluene',
            '30': 'Benzene',
            '35': 'Etilbenzene',
            '37': 'Metaxylene',
            '38': 'Paraxylene',
            '39': 'Orthoxylene',
            '42': 'Total Hydrocarbons',
            '43': 'Hydrocarbons - Methane',
            '44': 'Non-methane hydrocarbons - Hexane'
        }

        self.other_dict = {
            '80': 'ultravioletRadiation',
            '81': 'windSpeed',
            '82': 'windDirection',
            '83': 'temperature',
            '86': 'relativeHumidity',
            '87': 'atmosphericPressure',
            '88': 'solarRadiation',
            '89': 'precipitation',
            '92': 'acidRainLevel'
        }

        self.other_descriptions = {
            '80': 'Ultraviolet Radiation',
            '81': 'Wind Speed',
            '82': 'Wind Direction',
            '83': 'temperature',
            '86': 'Relative Humidity',
            '87': 'Atmospheric Pressure',
            '88': 'Solar Radiation',
            '89': 'Precipitation',
            '92': 'Acid Rain Level'
        }

        self.dataset_url = \
            'https://datos.madrid.es/egob/catalogo/212531-7916318-calidad-aire-tiempo-real.txt'

        # Statistics for tracking purposes
        self.persisted_entities = 0
        self.in_error_entities = 0

        self.FIWARE_SERVICE = fiware_service
        self.FIWARE_SERVICE_PATH = fiware_service_path

        # List of known air quality stations
        self.station_dict = {}
        self.read_station_csv()

        # Append the list of stations
        for station in stations:
            self.stations_to_retrieve_data.append(station)

    def get_persisted_entities(self):
        return self.persisted_entities

    def get_in_error_entities(self):
        return self.in_error_entities

    # Sanitize string to avoid forbidden characters by Orion
    @staticmethod
    def sanitize(str_in):
        return sub(r"[<(>)\"\'=;]", "", str_in)

    # Obtains air quality data and harmonizes it, persisting to Orion
    def get_air_quality_madrid(self):
        with closing(urlopen(url=self.dataset_url,
                             context=create_default_context(cafile=where())
                             )
                     ) as f:

            csv_data = f.read()
            csv_file = StringIO(csv_data.decode())
            data = reader(csv_file, delimiter=',')

            # Dictionary with station data indexed by station code
            # An array per station code containing one element per hour
            stations = {}

            for row in data:
                station_code = row[0] + row[1] + row[2]

                station_num = row[2]
                if not self.station_dict[station_num]:
                    continue

                if station_code not in stations:
                    stations[station_code] = []

                magnitude = row[3]

                if (magnitude not in self.pollutant_dict) and (
                        magnitude not in self.other_dict):
                    continue

                is_other = None
                if magnitude in self.pollutant_dict:
                    property_name = self.pollutant_dict[magnitude]
                    property_desc = self.pollutant_descriptions[magnitude]
                    is_other = False

                if magnitude in self.other_dict:
                    property_name = self.other_dict[magnitude]
                    property_desc = self.other_descriptions[magnitude]
                    is_other = True

                hour = 0

                for x in range(9, 57, 2):
                    value = row[x]
                    value_control = row[x + 1]

                    if value_control == 'V':
                        # A new entity object is created if it does not exist yet
                        if len(stations[station_code]) < (hour + 1):
                            stations[station_code].append(self.build_station(
                                station_num, station_code, hour, row))
                        elif 'id' not in stations[station_code][hour]:
                            stations[station_code][hour] = self.build_station(
                                station_num, station_code, hour, row)

                        param_value = float(value)

                        if not is_other:
                            unit_code = 'GQ'
                            if property_name == 'CO':
                                unit_code = 'GP'

                            measurand_data = [
                                property_name, str(param_value),
                                unit_code, property_desc]
                            stations[station_code][hour]['measurand']['value'] \
                                .append(','.join(measurand_data))
                        else:
                            if property_name == 'relativeHumidity':
                                param_value = param_value / 100

                        stations[station_code][hour][property_name] = {
                            'value': param_value
                        }
                    else:
                        # ensure there are no holes in the data
                        if len(stations[station_code]) < (hour + 1):
                            stations[station_code].append({})

                    hour += 1

            # Now persisting data to Orion Context Broker
            for station in stations:
                if self.stations_to_retrieve_data:
                    if station not in self.stations_to_retrieve_data:
                        continue
                station_data = stations[station]
                data_array = []
                for data in station_data:
                    if 'id' in data:
                        data_array.append(data)
                if len(data_array) > 0:
                    self.logger.debug("Retrieved data for %s at %s (last hour)",
                                      station, data_array[-1]['dateObserved']['value'])

                    # Last measurement is duplicated to have an entity with the
                    # latest measurement obtained
                    last_measurement = data_array[-1]
                    last_measurement['id'] = \
                        'Madrid-AirQualityObserved-' + \
                        last_measurement['stationCode']['value'] + '-' + 'latest'
                else:
                    self.logger.warning('No data retrieved for: %s', station)

                self.post_station_data(station, data_array)

    # Builds a new entity of type AirQualityObserved
    def build_station(self, station_num, station_code, hour, row):
        station_name = AirQualityObserved.sanitize(self.station_dict[station_num]['name'])
        street_address = AirQualityObserved.sanitize(self.station_dict[station_num]['address'])

        station_data = {
            'type': self.AMBIENT_TYPE_NAME,
            'measurand': {
                'type': 'List',
                'value': []
            },
            'stationCode': {
                'value': station_code
            },
            'stationName': {
                'value': station_name
            },
            'address': {
                'type': 'PostalAddress',
                'value': {
                    'addressCountry': 'ES',
                    'addressLocality': 'Madrid',
                    'streetAddress': street_address
                }
            },
            'location': {
                'type': 'geo:json',
                'value': self.station_dict[station_num]['location']['value'] or None
            },
            'source': {
                'type': 'URL',
                'value': 'http://datos.madrid.es'
            },
            'dataProvider': {
                'value': 'TEF'
            }
        }

        valid_from = datetime(int(row[6]), int(row[7]), int(row[8]), hour)
        station_data['id'] = 'Madrid-AirQualityObserved-' + \
                             station_code + '-' + valid_from.isoformat()
        valid_to = (valid_from + timedelta(hours=1))

        # Adjust timezones
        valid_from = valid_from.replace(tzinfo=self.madrid_tz)
        valid_to = valid_to.replace(tzinfo=self.madrid_tz)

        station_data['validity'] = {
            'value': {
                'from': valid_from.isoformat(),
                'to': valid_to.isoformat()
            },
            'type': 'StructuredValue'
        }

        station_data['hour'] = {
            'value': str(hour) + ':' + '00'
        }

        observ_corrected_date = valid_from
        station_data['dateObserved'] = {
            'type': 'DateTime',
            'value': observ_corrected_date.isoformat()
        }

        return station_data

    # POST data to an Orion Context Broker instance using NGSIv2 API
    def post_station_data(self, station_code, data):
        if len(data) == 0:
            return

        if self.only_latest:
            data_to_be_persisted = [data[-1]]
        else:
            data_to_be_persisted = data

        url = self.orion_service + '/v2/op/update'

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Fiware-Service': self.FIWARE_SERVICE,
            'Fiware-Servicepath': self.FIWARE_SERVICE_PATH
        }

        payload = {
            'actionType': 'append',
            'entities': data_to_be_persisted
        }

        # payload = dumps(payload).encode('ascii')

        self.logger.debug(
            'Going to persist %s to %s - %d',
            station_code,
            self.orion_service,
            len(data))

        try:
            r = post(url=url, json=payload, headers=headers)
            r.raise_for_status()

            self.logger.debug("Entity successfully created: %s", station_code)
            self.persisted_entities = self.persisted_entities + 1
        except HTTPError as e:
            self.logger.error("Http Error while POSTing data to Orion: {} - {}"
                              .format(e.response.status_code, e.response.reason))
            self.in_error_entities = self.in_error_entities + 1
        except ConnectionError as e:
            self.logger.error("Error Connecting to Orion: {}".format(e.strerror))
            self.in_error_entities = self.in_error_entities + 1
        except Timeout as e:
            self.logger.error("Timeout Error while POSTing data to Orion: {}".format(e.strerror))
            self.in_error_entities = self.in_error_entities + 1
        except RequestException as e:
            self.logger.error("Oops: Something else while POSTing data to Orion: {}".format(e.strerror))
            self.in_error_entities = self.in_error_entities + 1

    # Reads station data from CSV file
    def read_station_csv(self):
        with closing(
                open('madrid_airquality_stations.csv', 'r')) as csvfile:
            data = reader(csvfile, delimiter=',')
            _ = next(data)

            for row in data:
                station_code = row[2].zfill(3)
                station_name = row[3]
                station_address = row[4]
                station_coords = {
                    'type': 'geo:json',
                    'value': {
                        'type': 'Point',
                        'coordinates': [float(row[0]), float(row[1])]
                    }
                }

                self.station_dict[station_code] = {
                    'name': station_name,
                    'address': station_address,
                    'location': station_coords
                }

            self.station_dict['099'] = {
                'name': 'average',
                'address': None,
                'location': None
            }

    def summary(self):
        self.logger.debug('Number of entities persisted: %d', airQuality.get_persisted_entities())
        self.logger.debug('Number of entities in error: %d', airQuality.get_in_error_entities())
        self.logger.debug('#### Harvesting cycle finished ... ####')


def setup_logger():
    # Set up a specific logger with our desired output level
    logger = getLogger('Madrid')
    logger.setLevel(DEBUG)

    #  Add the log message handler to the logger
    handler = RotatingFileHandler(filename='harvest_madrid.log', maxBytes=2000000, backupCount=3)

    formatter = Formatter('%(levelname)s %(asctime)s %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


if __name__ == '__main__':
    my_logger = setup_logger()

    parser = ArgumentParser(description='Madrid air quality harvester')

    parser.add_argument('stations', metavar='stations', type=str, nargs='*',
                        help='Station Codes separated by spaces. ' +
                             ' the number can be derived from the map ' +
                             'https://jmcanterafonseca.carto.com/'
                             'viz/4a44801e-7bb2-41bc-b293-35ae2a7306f5/'
                             'public_map')

    parser.add_argument('--service', metavar='service', type=str, nargs=1,
                        help='FIWARE Service')

    parser.add_argument('--service-path', metavar='service_path',
                        type=str, nargs=1, help='FIWARE Service Path')

    parser.add_argument('--endpoint', metavar='endpoint', type=str, nargs=1,
                        help='Context Broker endpoint. '
                             'Example: http://orion:1026')

    parser.add_argument('--latest', action='store_true',
                        help='Flag to indicate to only '
                             'harvest the latest observation')

    parser.add_argument('--t0', metavar='t0', type=int, nargs=1, default=0,
                        help='Time to recover again the data in seconds. Default value 0 means no execution again. '
                             'Minimum value xxx ')

    args = parser.parse_args()

    FIWARE_SERVICE = None
    if args.service:
        FIWARE_SERVICE = args.service[0]
        my_logger.info('Fiware-Service: ' + FIWARE_SERVICE)

    FIWARE_SPATH = None
    if args.service_path:
        FIWARE_SPATH = args.service_path[0]
        my_logger.info('Fiware-Servicepath: ' + FIWARE_SPATH)

    orion_service = None
    if args.endpoint:
        orion_service = args.endpoint[0]
        my_logger.info('Context Broker: ' + orion_service)

    only_latest = False
    if args.latest:
        my_logger.info('Only retrieving latest observations')
        only_latest = True

    if args.t0 <= 1800 and args.t0 != 0:
        my_logger.error('The minimum waiting time to execute the harvest again is 1800 seconds.')
        exit(-1)
    elif args.t0 == 0:
        # The process is executed only once
        airQuality = AirQualityObserved(logger=my_logger,
                                        stations=args.stations,
                                        fiware_service=FIWARE_SERVICE,
                                        fiware_service_path=FIWARE_SPATH,
                                        endpoint=orion_service,
                                        only_latest=only_latest)

        airQuality.get_air_quality_madrid()

        airQuality.summary()
    else:
        # The process is executed every args.t0 seconds without end. It is recommended
        # to have the parameter --latest in that case
        if only_latest == False:
            my_logger.error("With continuous execution the parameter --latest MUST be indicated")
            exit(-1)
        while True:
            my_logger.info("New circle started")
            airQuality = AirQualityObserved(logger=my_logger,
                                            stations=args.stations,
                                            fiware_service=FIWARE_SERVICE,
                                            fiware_service_path=FIWARE_SPATH,
                                            endpoint=orion_service,
                                            only_latest=only_latest)

            airQuality.get_air_quality_madrid()

            airQuality.summary()

            my_logger.info("Sleep for {} seconds".format(args.t0))
            sleep(args.t0)

