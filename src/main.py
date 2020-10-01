#!/usr/bin/env python3

import configparser
import logging
from pathlib import Path
import csv, sys
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
    folder1: Path = Path()
    folder2: Path = Path()
    # config parser
    config = configparser.ConfigParser()

    @staticmethod
    def exitError(error_string):
        """ Produce error and exit. """
        logging.error(error_string)
        sys.exit(1)

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
        self.folder1 = Path(self.loadValueFromConfig('subdir', 'folder1'))
        self.folder2 = Path(self.loadValueFromConfig('subdir', 'folder2'))
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

    @staticmethod
    def writeRowToErrorCSV(row: List[str], writer_handle: csv.writer):
        """ Write a column to CSV """
        writer_handle.writerow(row)

    @staticmethod
    def handleInputCSV(input_csv, row_callback):
        logging.info(f'Handling input CSV {input_csv}')
        """ Read pathfile for main paths. """
        with open(input_csv, 'r') as read_obj:
            csv_reader = csv.reader(read_obj)
            for row in csv_reader:
                row_callback(row)

    @staticmethod
    def mkdir(path: Path):
        try:
            path.mkdir(parents=True)
        except FileExistsError:
            logging.warning(f'Attempted to create {path}, but it already exists!')

    # noinspection DuplicatedCode
    def handleRowMain(self, row: list):
        """ Handle row in main input CSV. """
        dir_name = row[0]
        if dir_name not in self.main_encountered_names:
            self.main_encountered_names.add(dir_name)
            to_create = Path(self.target_path / dir_name)
            logging.info(f'Creating path: {to_create}')
            self.mkdir(to_create)
        else:
            self.writeRowToErrorCSV([dir_name], self.csv_errorfile_main_writer)

    # noinspection DuplicatedCode
    def handleRowNested(self, row: list):
        """ Handle row in nested input CSV. """
        dir_name = row[0]
        try:
            nested_dir_name = row[1]
        except IndexError:
            self.writeRowToErrorCSV([dir_name], self.csv_errorfile_nested_writer)
            return False
        if dir_name not in self.nested_encountered_names:
            self.nested_encountered_names.add(dir_name)
            to_create = Path(self.target_path / dir_name / self.folder1 / nested_dir_name)
            logging.info(f'Creating path: {to_create}')
            self.mkdir(to_create)
            to_create = Path(self.target_path / dir_name / self.folder2 / nested_dir_name)
            logging.info(f'Creating path: {to_create}')
            self.mkdir(to_create)
        else:
            self.writeRowToErrorCSV([dir_name], self.csv_errorfile_nested_writer)

    def run(self):
        """ Run program. """
        self.setupLogging()
        logging.info('Loading config...')
        self.loadConfig()
        logging.info('Opening error CSVs...')
        self.openErrorCSVs()
        logging.info('Reading main CSV...')
        self.handleInputCSV(self.csv_pathfile_main, self.handleRowMain)
        logging.info('Reading nested CSV...')
        self.handleInputCSV(self.csv_pathfile_nested, self.handleRowNested)


if __name__ == '__main__':
    process = Process()
    process.run()
