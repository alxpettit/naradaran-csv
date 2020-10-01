#!/usr/bin/env python3

import configparser
import csv
import logging
import sys
from os import getcwd, remove
from pathlib import Path
from typing import Set
import shutil


class Process:
    # The path to the config file.
    config_file_path: str = Path('config.ini')
    # The path to which we output our log file for debugging purposes
    # I am assuming client does not want to use a terminal to see STDERR/STDOUT.
    log_file_name: Path = Path('debug.log')
    csv_first_encountered_ids: Set[str] = set()
    csv_second_encountered_ids: Set[str] = set()

    # IDK paths
    csv_pathfile_first: Path = Path()
    csv_pathfile_second: Path = Path()
    csv_third: Path = Path()

    # The path to which to write.
    work_path: Path = Path()

    # The paths from which to copy
    copy_from_path1: Path = Path()
    copy_from_path2: Path = Path()

    current_id: str = ''

    csv_second_encountered_subids: Set[str] = set()

    # We add errored directory names to these CSVs
    csv_errorfile_first: Path = Path()
    csv_errorfile_second: Path = Path()
    csv_errorfile_third: Path = Path()
    csv_errorfile_first_writer: csv.writer = None
    csv_errorfile_second_writer: csv.writer = None
    csv_errorfile_third_writer: csv.writer = None
    project_homepage: Path = Path()
    individual_gate: Path = Path()
    logging_level: int = None
    # config parser
    config = configparser.ConfigParser()

    @staticmethod
    def exitError(error_string):
        """ Produce error and exit. """
        logging.error(error_string)
        sys.exit(2)

    def loadValueFromConfig(self, section: str, key: str, default_value: str):
        """ Load values from our config file, terminating in event of error. """
        try:
            return self.config[section][key]
        except KeyError:
            logging.info(f'Could not load section {section}, key {key} from config file.')
            logging.info(f'Defaulting to "{default_value}".')
            if section not in self.config.sections():
                self.config.add_section(section)
            self.config.set(section, key, default_value)
            return default_value

    def loadPathFromConfig(self, section, key, nonexistent: bool = False, default_value: str = ''):
        value = self.loadValueFromConfig(section, key, default_value=default_value)
        abs_path = Path(value).absolute()
        if abs_path.exists() or nonexistent:
            return abs_path
        else:
            self.exitError(f'File specified under section "{section}",\nkey "{key}" ({abs_path}) does not exist!')

    def loadConfig(self):
        """ Load our config file. """
        if not Path(self.config_file_path).exists():
            logging.warning(f'The config file {self.config_file_path} is missing!')
        else:
            self.config.read(self.config_file_path)

        # Names are very confusing, but that's how it is sometimes with commissions! :)
        # Originally these configs were entirely controlled by config file, but then client asked to hardcode defaults
        # Should probably refactor to saner system but since it's a one-time use thing...
        self.csv_pathfile_first = self.loadPathFromConfig('csv_pathsfiles', 'path_first', default_value='First.csv')
        self.csv_errorfile_first = self.loadPathFromConfig('csv_errorfiles', 'path_first', nonexistent=True,
                                                           default_value='First_error.csv')
        self.csv_pathfile_second = self.loadPathFromConfig('csv_pathsfiles', 'path_second', default_value='Second.csv')
        self.csv_errorfile_second = self.loadPathFromConfig('csv_errorfiles', 'path_second', nonexistent=True,
                                                            default_value='Second_error.csv')
        self.csv_errorfile_third = self.loadPathFromConfig('csv_errorfiles', 'path_third', nonexistent=True,
                                                           default_value='Third_error.csv')
        self.csv_third = self.loadPathFromConfig('csv_pathsfiles', 'path_third', default_value='Third.csv')
        self.project_homepage = Path(self.loadValueFromConfig('subdir', 'project_homepage',
                                                              'Project Homepage Attachments'))
        self.individual_gate = Path(self.loadValueFromConfig('subdir', 'individual_gate',
                                                             'Individual Gate Quest Attachments'))
        self.work_path = self.loadPathFromConfig('work', 'path', default_value='/temp/project/results/')
        self.copy_from_path1 = self.loadPathFromConfig('copyfrom', 'path1', default_value='/temp/project/temp1/')
        self.copy_from_path2 = self.loadPathFromConfig('copyfrom', 'path2', default_value='/temp/project/temp2/')
        self.logging_level = int(self.loadValueFromConfig('logging', 'log_level', default_value=str(logging.WARNING)))

    def setupLogging(self):
        """ Set up default logging object. """
        # noinspection PyArgumentList
        logging.basicConfig(
            level=self.logging_level,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(self.log_file_name),
                logging.StreamHandler()
            ]
        )

    def openErrorCSV(self, errorfile: Path):
        if errorfile.exists():
            remove(errorfile)
        else:
            self.mkdir(errorfile.parent, parents=True)
        return csv.writer(open(errorfile, 'w'))

    def openErrorCSVs(self):
        """ Open CSVs and create writer objects. """
        self.csv_errorfile_first_writer = self.openErrorCSV(self.csv_errorfile_first)
        self.csv_errorfile_second_writer = self.openErrorCSV(self.csv_errorfile_second)
        self.csv_errorfile_third_writer = self.openErrorCSV(self.csv_errorfile_third)

    def handleErroredID(self, writer_handle: csv.writer, doc_name, error_type):
        """ Write a column to CSV """
        writer_handle.writerow([self.current_id, error_type, doc_name])
        logging.warning(f'Encountered error in "{doc_name}" of type "{error_type}". ID is {self.current_id}')

    @staticmethod
    def handleInputCSV(input_csv: csv.reader, row_callback):
        logging.info(f'Handling input CSV {input_csv}')
        """ Read pathfile for main paths. """
        with open(input_csv, 'r') as read_obj:
            csv_reader = csv.reader(read_obj)
            for row in csv_reader:
                row_callback(row)

    @staticmethod
    def mkdir(path: Path, parents: bool) -> object:
        try:
            path.mkdir(parents=parents)
        except FileExistsError:
            logging.warning(f'Attempted to create {path}, but it already exists!')
            return False
        except FileNotFoundError:
            logging.warning(f'Attempted to create {path}, but parent directory doesn\'t exist!')
            return False
        return True

    def copytree(self, src: Path, dst: Path, writer_handle: csv.writer, doc_name: str):
        if src.exists():
            try:
                logging.info(f'Copying: {src} -> {dst}')
                shutil.copytree(src, dst, dirs_exist_ok=True)
            except OSError as os_error:
                # probably means directory didn't exist
                logging.info(f'OSError raised: {os_error} while copying:')
                logging.info(f'{src} -> {dst}')
                self.handleErroredID(writer_handle=writer_handle,
                                     doc_name=doc_name, error_type='OS_ERROR')
        else:
            self.handleErroredID(writer_handle=writer_handle,
                                 doc_name=doc_name, error_type='FILE_NOT_EXIST')

    def handleRowFirstCSV(self, row: list):
        """ Handle row in main input CSV. """
        self.current_id = row[0]
        # "First.csv will give the name of one folder to be created under
        # say c:\temp\project For example - c:\temp\project\12354
        # Under this folder you will create 2 more empty new folders.
        # Folder names of these 2 folders is provided by config file.
        # Let the folder names be Project Homepage Attachments and Individual Gate Quest Attachments.
        # These are 2 common folders that will exist in every folder provided by First.csv" -- client
        if self.current_id not in self.csv_first_encountered_ids:
            self.csv_first_encountered_ids.add(self.current_id)
            id_save_path = Path(self.work_path / self.current_id)
            for subdir in [self.project_homepage, self.individual_gate]:
                to_create = id_save_path / subdir
                logging.info(f'Creating path: {to_create}')
                self.mkdir(to_create, parents=True)
            # "Now - you have already read the folder name 12354 -
            # Search this folder in a new path C:\temp\Project\temp1. This path is given via config
            # When you find the folder in this new path, copy that folder to "Project Homepage Attachments"
            # For example, after copy, it will look like c:\temp\project\12354\Project Homepage Attachments\12354"
            # -- client
            src: Path = self.copy_from_path1 / self.current_id
            dst: Path = id_save_path / self.project_homepage / self.current_id
            self.copytree(src, dst, writer_handle=self.csv_errorfile_first_writer, doc_name='FirstCSV')
        else:
            self.handleErroredID(writer_handle=self.csv_errorfile_first_writer,
                                 doc_name='FirstCSV', error_type='DUPLICATE_ENTRY')

    def handleRowSecondCSV(self, row: list):
        """ Handle row in nested input CSV. """
        self.current_id = row[0]
        if self.current_id in self.csv_first_encountered_ids:
            if self.current_id not in self.csv_second_encountered_ids:
                id_save_path = Path(self.work_path / self.current_id)
                # "Now, take the same folder name (12354 from First.csv) and search Second.csv.
                # For every find, you will find multiple different unique folder names listed in column 2 of Second.csv.
                # Read those different unique folder names from column2 corresponding to column1
                # (which is essentially First.csv, also look like numbers)" -- client

                # "Now, and search these new folders -
                # each and every one of them in c:\temp\project\temp2 (different path and folders)
                # When you find these folders,
                # copy those folders directly into Individual Gate Quest Attachments." -- client

                if len(row) > 1:
                    for column in row[1:]:
                        self.current_id = column
                        if self.current_id not in self.csv_second_encountered_subids:
                            self.csv_second_encountered_subids.add(column)
                            id_save_path2: Path = Path(column)
                            src: Path = self.copy_from_path2 / id_save_path2
                            dst: Path = id_save_path / self.individual_gate / id_save_path2
                            self.copytree(src, dst, writer_handle=self.csv_errorfile_second_writer,
                                          doc_name='SecondCSV')
                        else:
                            self.handleErroredID(writer_handle=self.csv_errorfile_second_writer,
                                                 doc_name='Second CSV', error_type='DUPLICATE_SUBID')
                else:
                    self.handleErroredID(writer_handle=self.csv_errorfile_second_writer,
                                         doc_name='SecondCSV', error_type='NO_ENTRIES')
            else:
                self.handleErroredID(writer_handle=self.csv_errorfile_second_writer,
                                     doc_name='SecondCSV', error_type='ENTRY_MISSING_FROM_FIRST_CSV')

    def handleThirdCSV(self):
        logging.info(f'Handling input CSV {self.csv_third}')
        """ Read pathfile for main paths. """
        with open(self.csv_third, 'r', encoding='latin1') as read_obj:
            csv_reader = csv.reader(read_obj)
            _ = next(csv_reader)  # header
            for row_num, row in enumerate(csv_reader):
                try:
                    node_id = row[0]
                    dir_name = row[1]
                    file_name = row[2]
                except IndexError:
                    logging.warning(f'Warning! Missing entries in row {row_num} of ThirdCSV.')
                test_path = Path(self.work_path / node_id / dir_name / file_name)
                if not test_path.exists():
                    self.current_id = dir_name
                    self.handleErroredID(writer_handle=self.csv_errorfile_third_writer,
                                         doc_name=test_path, error_type='ERROR_MISSING_FILE')

    def main(self):
        """ Run program. """
        self.setupLogging()
        logging.info(f'Program started. Working directory: {getcwd()}')
        logging.info('Loading config...')
        self.loadConfig()
        logging.info('Opening error CSVs...')
        self.openErrorCSVs()
        logging.info('Reading first CSV...')
        self.handleInputCSV(self.csv_pathfile_first, self.handleRowFirstCSV)
        logging.info('Reading second CSV...')
        self.handleInputCSV(self.csv_pathfile_second, self.handleRowSecondCSV)
        logging.info('Reading third CSV...')
        self.handleThirdCSV()


if __name__ == '__main__':
    process = Process()
    # noinspection PyBroadException
    try:
        process.main()
    except Exception as e:
        logging.error('Unhandled exception in main()', exc_info=True)
        exit(1)
