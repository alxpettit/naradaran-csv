#!/usr/bin/env python3

import configparser
import logging
from pathlib import Path
import csv
from typing import List, Set


class Process:
    # The path to the config file.
    config_file_path: str = Path('config.ini')
    # The path to which we output our log file for debugging purposes
    # I am assuming client does not want to use a terminal to see STDERR/STDOUT.
    log_file_name: Path = Path('debug.log')
    main_encountered_names: Set[str] = set()
    nested_encountered_names: Set[str] = set()
    # The CSV file containing info on main paths.
    csv_pathfile_main: Path = Path()
    # The CSV file containing info for information under the main paths.
    csv_pathfile_nested: Path = Path()
    # The path to which to write.
    target_path: Path = Path()
    # We add errored directory names to these CSVs
    csv_errorfile_main: Path = Path()
    csv_errorfile_nested: Path = Path()
    csv_errorfile_main_writer: csv.writer = None
    csv_errorfile_nested_writer: csv.writer = None
    # config parser
    config = configparser.ConfigParser()

    @staticmethod
    def exitError(error_string):
        """ Produce error and exit. """
        logging.error(error_string)
        exit(1)

    def loadValueFromConfig(self, key: str, value: str):
        """ Load values from our config file, terminating in event of error. """
        try:
            return self.config[key][value]
        except KeyError:
            self.exitError(f'Could not load {key}, value {value} from config file.')

    def loadPathFromConfig(self, key, value, nonexistent=False):
        abs_path = Path(self.loadValueFromConfig(key, value)).absolute()
        if abs_path.exists() or nonexistent:
            return abs_path
        else:
            self.exitError(f'File specified under key {key}, value {value} does not exist!')

    def loadConfig(self):
        """ Load our config file, terminating in event of error. """
        if not Path(self.config_file_path).exists():
            self.exitError(f'The config file {self.config_file_path} is missing!')
        self.config.read(self.config_file_path)

        self.csv_pathfile_main = self.loadPathFromConfig('csv_pathsfiles', 'path_main')
        self.csv_pathfile_nested = self.loadPathFromConfig('csv_pathsfiles', 'path_nested')
        self.csv_errorfile_main = self.loadPathFromConfig('csv_errorfiles', 'path_main', nonexistent=True)
        self.csv_errorfile_nested = self.loadPathFromConfig('csv_errorfiles', 'path_nested', nonexistent=True)
        self.target_path = self.loadPathFromConfig('target', 'path')

    def setupLogging(self):
        """ Set up default logging object. """
        # noinspection PyArgumentList
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(self.log_file_name),
                logging.StreamHandler()
            ]
        )

    def openErrorCSVs(self):
        """ Open CSVs and create writer objects. """
        self.csv_errorfile_main_writer = csv.writer(open(self.csv_errorfile_main, 'w'))
        self.csv_errorfile_nested_writer = csv.writer(open(self.csv_errorfile_nested, 'w'))

    def writeRowToErrorCSV(self, row: List[str], writer_handle: csv.writer):
        """ Write a column to CSV """
        writer_handle.writerow(row)

    # No time for polishing!
    # noinspection DuplicatedCode
    def readMain(self):
        """ Read pathfile for main paths. """
        with open(self.csv_pathfile_main, 'r') as read_obj:
            csv_reader = csv.reader(read_obj)
            for row in csv_reader:
                dir_name = row[0]
                if dir_name not in self.main_encountered_names:
                    self.main_encountered_names.add(dir_name)
                    to_create = Path(self.target_path / dir_name)
                    logging.info(f'Creating path: {to_create}')
                    try:
                        to_create.mkdir(parents=True)
                    except FileExistsError:
                        logging.warning(f'Attempted to create {to_create}, but it already exists!')
                else:
                    self.writeRowToErrorCSV([dir_name], self.csv_errorfile_main_writer)

    # No time for polishing!
    # noinspection DuplicatedCode
    def readNested(self):
        """ Read pathfile for nested paths. """
        with open(self.csv_pathfile_nested, 'r') as read_obj:
            csv_reader = csv.reader(read_obj)
            for row in csv_reader:
                dir_name = row[0]
                if dir_name not in self.nested_encountered_names:
                    self.nested_encountered_names.add(dir_name)
                    to_create = Path(self.target_path / dir_name)
                    logging.info(f'Creating path: {to_create}')
                    try:
                        to_create.mkdir(parents=True)
                    except FileExistsError:
                        logging.warning(f'Attempted to create {to_create}, but it already exists!')
                else:
                    self.writeRowToErrorCSV([dir_name], self.csv_errorfile_nested_writer)

    def run(self):
        """ Run program. """
        self.setupLogging()
        logging.info('Loading config...')
        self.loadConfig()
        logging.info('Opening error CSVs...')
        self.openErrorCSVs()
        logging.info('Reading M')
        self.readMain()


if __name__ == '__main__':
    process = Process()
    process.run()
