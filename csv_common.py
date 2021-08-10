"""
This contains the base_csv_file class, and other auxillary functions that
the standards package uses.

The base_csv_file is the base for any of the Character Seperated
Value files that this standards library contains.

Examples:

.. code-block:

    # example reading of basic csv file
    from standards.common import base_csv_file
    headers=['id', 'name', 'data']
    test = base_csv_file("test.csv", headers, headers)
    test.setup_read()
    for value in test.readrow():
        print(value)


    # example reading of a clarity file
    from standards.clarity_extract2 import extract_file
    clarity = extract_file("hannon_provider_patients_in_epic.csv")
    clarity.setup_read()
    clarity_data = clarity.read_by_name_ssn()
    print ("# of records: %s" % len(clarity_data))
    for entry in clarity_data:
        print ("Contact Date: ", entry["CONTACT_DATE"])
        print ("Visit Prov Id: ", entry["VISIT_PROV_ID"])

Versions:
    v1.56 - Default CSV Writer to use QUOTE_MINIMAL, controlled by quote argument
    v1.55 - Added in_sep & out_sep to mdy_to_ymd_str
          - Added out_sep to float_to_ymd_str

    v1.5 - Added ConflictCount, and readCount in BaseCsvFile.

    v1.0 - General Release

"""
__author__ = "Benjamin Schollnick"
__status__ = "Production"
__version__ = "1.55"


import datetime
import csv
import pathlib
import os
import sys

from dateutil.parser import parse
from dateutil.parser._parser import ParserError


def ensure_dirs(dpath):
    """
    If the directory path does not exist,
    then create it!
    """
    try:
        os.makedirs(dpath)
    except WindowsError:
        pass

def force_add_seps(datestring, sep="-"):
    """Must be yyyymmdd

    """
    return datestring[0:4] + sep + datestring[4:6] + sep + datestring[6:]

def mdy_to_ymd_str(mdy, in_sep="-", out_sep="-"):
    """
    Convert from mm/dd/yyyy datetime date string to a yyyy-mm-dd string.

    Args:
        mdy (string): The DateTime date string (%m-%d-%Y) to be converted
        def_sep (string): The default separator character between the values
            by default that is "-" for the inbound string

        out_sep (string): The default separator character between the values
            by default that is "-" for the outbound string

        reject_blank (Boolean): If True, if the date can not be parsed, return None
                                If False, the existing mdy value will be returned

                           Thus if False, invalid data can be returned (it's the
                           original data that was sent into the function)

    Returns:
        datetime: string
            in yyyy-mm-dd format (assuming it's not overriden by out_sep)

    .. code-block:

    >>> import datetime
    >>> test = datetime.datetime(2018,1,1).strftime("%m-%d-%Y")
    >>> mdy_to_ymd_str(test)
    '2018-01-01'
    >>> mdy_to_ymd_str("08-26-2019")
    '2019-08-26'
    >>> common.mdy_to_ymd_str("08-24-2019")
    '2019-08-24'
    >>> common.mdy_to_ymd_str("08-24-2019", out_sep="/")
    '2019/08/24'
    >>> common.mdy_to_ymd_str("08*24*2019", in_sep="*", out_sep="/")
    '2019/08/24'
    """
    output = ""
    if mdy not in [None, ""]:
        try:
            output = datetime.datetime.strptime(mdy, "%m{}%d{}%Y".format(in_sep, in_sep))
            output = output.strftime("%Y{}%m{}%d".format(out_sep, out_sep))
        except ValueError:
            return None
    return output

def mdy_to_ymd_flex_str(mdy, in_sep=r"-", out_sep="-", yearFirst=False, dayFirst=False, reject_blank=False, default_yr=2000):
    """
    Convert from mm/dd/yyyy datetime date string to a yyyy-mm-dd string.

    see https://github.com/dateutil/dateutil/issues/703# regarding dateutils defaulting of century.

    Args:
        mdy (string): The DateTime date string (%m-%d-%Y) to be converted
        def_sep (string): A string of separator characters that should be removed.

        out_sep (string): The default separator character between the values
            by default that is "-" for the outbound string

        reject_blank (Boolean): If True, if the date can not be parsed, return None
                                If False, the existing mdy value will be returned

                           Thus if False, invalid data can be returned (it's the
                           original data that was sent into the function)

    Returns:
        datetime: string
            in yyyy-mm-dd format (assuming it's not overriden by out_sep)

    .. code-block:

    >>> import datetime
    >>> test = datetime.datetime(2018,1,1).strftime("%m-%d-%Y")
    >>> mdy_to_ymd_flex_str(test)
    '2018-01-01'
    >>> mdy_to_ymd_flex_str("08-26-2019")
    '2019-08-26'
    >>> common.mdy_to_ymd_flex_str("08-24-2019")
    '2019-08-24'
    >>> common.mdy_to_ymd_flex_str("08-24-2019", out_sep="/")
    '2019/08/24'
    >>> common.mdy_to_ymd_flex_str("08*24*2019", in_sep="*", out_sep="/")
    '2019/08/24'
    """

    from dateutil.parser import parserinfo, parser
    class parserinfo_20c(parserinfo):
        def convertyear(self, year, century_specified=False):
            if not century_specified and year < 100:
                year += default_yr
            return year

    parser_20c = parser(parserinfo_20c())

    def parse_20c(timestr, **kwargs):
        return parser_20c.parse(timestr, **kwargs)
            # mm-dd-yyyy    # 10    -> mmddyyyy     # 8
            # mm-dd-yy      # 8     -> mmddyy       # 6
            # mmddyy        # 6     -> mmddyy       # 6

    mdy = mdy.replace(in_sep, "-")
    if mdy not in [None, ""]:
        try:
            mdy = parse_20c(mdy, yearfirst=yearFirst, dayfirst=dayFirst).strftime("%Y{}%m{}%d".format(out_sep, out_sep)) # if out_seps requested, they are added.
        except ParserError:
            mdy = False
            print("Parser Error")
            if reject_blank:
                return None
    return mdy

def float_to_ymd_str(float_value, out_sep="-"):
    """
    Convert from floating point string (epoch) to a yyyy-mm-dd string.

    Args:
        float_value (float): The DateTime floating point (epoch timestamp) value

    Returns:
        datetime: string in yyyy-mm-dd format

    .. code-block:

    >>> float_to_ymd_str(1514786400.00)
    '2018-01-01'
    """
    output = datetime.datetime.fromtimestamp(float_value)
    output = output.strftime("%Y{}%m{}%d".format(out_sep, out_sep))
    return output

class BaseCsvFile():
    """
        Base class for xSV functionality.

     """
    def __init__(self, fqpn, input_headers=None,
                 output_headers=None, padlength=8, padchar='0',
                 lineterminator='\n'):
        """
        Args:
            fqpn (string): Fully Qualified PathName
            input_headers (list): Override autodetection of csv headers.
                contains the headers in the order of the headers in the file.
            output_headers (list): contains the headers in the order of the
                headers in the output file.
            padlength (integer): Number of characters in the EMRN, defaults to 8
            padchar (string): The character(s) to pad with
            lineterminator (string): The character to use to terminate the csv
                line with.

        For the fqpn, as long as it's a valid pathname from the app
            directory, it will be useable.

        eg:

            * c:/test.csv
            * c:/users/text.csv
            * test.csv
            * p:t.csv
        """
        self.path = pathlib.Path(fqpn)
        self.__fh = None
        self.reading = False
        self.writing = False
        self.csv_handler = None
        self.input_headers = input_headers
        self.output_headers = output_headers
        self.padlength = padlength
        self.padchar = padchar
        self.quoting = csv.QUOTE_ALL
        #self.quoting = csv.QUOTE_NONNUMERIC
        self.lineterm = lineterminator
        self.conflictCount = 0
        self.readCount = None
        self.source = None
        self.allow_append = False

    def quote_all(self):
        self.quoting = csv.QUOTE_ALL

    def quote_minimal(self):
        self.quoting = csv.QUOTE_MINIMAL

    def quote_nonnumeric(self):
        self.quoting = csv.QUOTE_NONNUMERIC

    def quote_none(self):
        self.quoting = csv.QUOTE_NONE

    def close(self):
        """
        Close the file handle
        """
        if self.__fh != None:
            self.__fh.close()

    def setup_read(self, delimiter=',', force_headers=False,
                   remap_source=False, encoding='utf-8-sig'):
        """
        Configure for Read only.

        Args:
            delimiter (String): The delimiting character for the CSV file.
                By default this is set to a Comma (,)

            force_headers (boolean): If True, do not auto-detect the headers,
                use the headers from self.input_headers.  If False, auto-detect.

            remap_source (function): If set to False (Boolean), then do not
                remap, use the file handle normally based off self.path.  If
                remap is intended, pass the function you wish to act as the file
                handle.  (Generally used for Memory IO, instead of File IO)

        Returns:
            Boolean: True if successfully set, False if bad headers, or
                File doesn't exist.

        Raises:
            RuntimeError: if already configured for reading.
                (This prevents, accidental reconfiguration to a different
                delimiter.)



        *Note*
            The init function will only set the variables.  You'll need
            to call setup_read() or setup_write() to configure for those
            purposes.

        https://stackoverflow.com/questions/34399172/
            why-does-my-python-code-print-the-extra-characters-%C3%AF-when-reading-from-a-tex/
        """
        if self.reading:
            raise RuntimeError("Duplicate Request - Already setup for Reading.")
        elif self.writing:
            raise RuntimeError("Configured for Writing - unable to Read.")

        if self.path.exists() is False:
            raise RuntimeError("File Does not Exist")
            #return False

        if encoding == None:
            self.__fh = self.path.open(mode='r', newline='')
        else:
            self.__fh = self.path.open(mode='r', newline='', encoding=encoding)

        if remap_source:
            self.source = remap_source(self.__fh)
        else:
            self.source = self.__fh

        if force_headers:
            self.csv_handler = csv.DictReader(self.source,
                                              delimiter=delimiter,
                                              fieldnames=self.input_headers,
                                              quoting=self.quoting,
                                              lineterminator=self.lineterm)
        else:
            self.csv_handler = csv.DictReader(self.source,
                                              delimiter=delimiter,
                                              quoting=self.quoting,
                                              lineterminator=self.lineterm)
        self.allow_append = False
        self.reading = True
        return True

    def setup_write(self, delimiter=',',
                    overwrite=True,
                    writeheader=True,
                    quoting=True):
        """
        Configure for Write only.

        Args:
            delimiter (string): The delimiting character for the CSV file. By default
                this is set to a comma (,)
            overwrite (boolean): Allow overwriting of files.  If set to False, and the
                file already exists, a RuntimeError will occur. *By Default this
                is set to True, and will overwrite files.*
            writeheader (Boolean): Write a header to the CSV file, if set to False,
                the header will be surpressed.
            quoting (Boolean): If True (Default), all non-float values will be quoted
                automatically in the CSV

        Returns:
            Boolean: True if successfully set, False if the file already
                          exists, and overwrite is set to False.

        Raises:
            RuntimeError: if already configured for writing.
                (This prevents, accidental reconfiguration to a different
                delimiter.)

        *Note*: This will overwrite any existing file without warning, by
        default.  Set overwrite to False, if you do not wish to overwrite.
        """
        if quoting:
            quote_level = self.quoting
        else:
            quote_level = csv.QUOTE_NONE

        if self.writing:
            raise RuntimeError("Duplicate Request - Already setup for Writing.")
        elif self.reading:
            raise RuntimeError("Configured for Reading - unable to Write.")
        if self.path.exists() and overwrite is False:
            return False
        self.__fh = self.path.open(mode='w', newline='')
        self.csv_handler = csv.DictWriter(self.__fh,
                                          delimiter=delimiter,
                                          fieldnames=self.output_headers,
                                          quoting=quote_level)
        if writeheader:
            self.csv_handler.writeheader()

        self.allow_append = False
        self.writing = True
        return True

    def setup_append(self, delimiter=',',
                    writeheader=True,
                    quoting=True):
        """
        Configure for Write only.

        Args:
            delimiter (string): The delimiting character for the CSV file. By default
                this is set to a comma (,)
            overwrite (boolean): Allow overwriting of files.  If set to False, and the
                file already exists, a RuntimeError will occur. *By Default this
                is set to True, and will overwrite files.*
            writeheader (Boolean): Write a header to the CSV file, if set to False,
                the header will be surpressed.
            quoting (Boolean): If True (Default), all non-float values will be quoted
                automatically in the CSV

        Returns:
            Boolean: True if successfully set, False if the file already
                          exists, and overwrite is set to False.

        Raises:
            RuntimeError: if already configured for writing.
                (This prevents, accidental reconfiguration to a different
                delimiter.)

        *Note*: This will overwrite any existing file without warning, by
        default.  Set overwrite to False, if you do not wish to overwrite.
        """
        self.allow_append = True
        if quoting:
            quote_level = self.quoting
        else:
            quote_level = csv.QUOTE_NONE

        if self.reading:
            raise RuntimeError("Configured for Reading - unable to Write.")
        if self.path.exists() and self.allow_append is False:
            return False
        already_exists = self.path.exists()
        self.__fh = self.path.open(mode='a', newline='')
        self.csv_handler = csv.DictWriter(self.__fh,
                                          delimiter=delimiter,
                                          fieldnames=self.output_headers,
                                          quoting=quote_level)
        if writeheader and already_exists == False:
            self.csv_handler.writeheader()

        self.writing = True
        return True

    def clear_record(self):
        """
        Return a dictionary that contains the headers (as key),
        and empty values.

        This way, you can populate the fields that need to be populated
        without the worry of missing a field.
        """
        output = {}
        for field in self.output_headers:
            output[field] = ""
        return output

    def flush(self):
        self.__fh.flush()

    def return_beginning(self):
        """
        Forcibly reset the file offset pointer to the beginning of the file.
        """
        self.__fh.seek(0)

    def readrow(self):
        """
        Read a CSV row from the reading file.

        Returns:
            Dictionary: Dictionary with the data from the CSV row.

        Raises:
            RuntimeError: if not configured for reading.

        .. code-block:

            from standards.universal import IndexFile
            stats = {}
            index_reader = IndexFile("test.csv")
            index_reader.setup_read()
            for row in index_reader.readrow():
                if row["doc_category"] not in stats:
                    stats[row["doc_category"]] = 0
                stats[row["doc_category"]] += 1

            for key in sorted(stats):
                print ("%s - %s" % (key, humanize.intcomma(stats[key])))
        """
        if not self.reading:
            raise RuntimeError('Attempted to Read without Setup')
        return self.csv_handler

    def write_cleaning(self, datadict):
        """
        *Subclass* if you need to force the datadictionary to follow specific
        rules.

        This will allow you to clean or replace/substitute the raw data before
        it is written.  (eg. pad data if not handled at read time, etc)

        Args:
            datadict (dictionary): The Row data that is being examined for
                cleaning.

        Returns:
            dictionary: The cleaned data

        Make sure to set clean TRUE in writerow to enable this functionality.

        See Universal.py for example.

        .. code-block:

            def write_cleaning(self, datadict):
                datadict["dob"] = datadict["dob"].replace("-", "")
                return datadict

        .. code-block:

            def writerow(self, datadict, clean=True):
                if self.reading:
                    raise RuntimeError("Configured for reading -- Unable to write.")
                return super().writerow(datadict, clean)
        """
        return datadict

    def readrawline(self, clean_func=None):
        """
        Allow manual loading of the file, line by line as a generator.
        This way you can still use the framework, but allows you to read
        in a specialized manner. (eg. not via read_by_key(s) )

        Args:
            clean_func (function):  Defaults to None (unused).
                If passed an function, that function will be called to process
                and manipulate the data, and then the data will be returned.

        Yield:
            dictionary: The dictionary for the row that is being read.
        """
        for row in self.csv_handler:
            if clean_func is not None:
                row = clean_func(row)
            yield row

    def writerow(self, datadict, clean=False):
        """
        Write a CSV row to the output file.

        Args:
            datadict (dictionary): The Row of Data to be written to the file
            clean (Boolean): If True, use write_cleaning routines

        Returns:
            Dictionary: The returned results from the csvdictwriter writerow

        Raises:
            RuntimeError: if not configured for reading.
        """
        if not self.writing:
            raise RuntimeError('Attempted to Write without Setup')
        if clean:
            datadict = self.write_cleaning(datadict)
        return self.csv_handler.writerow(datadict)

    def getReadCount(self):
        """
        Please note, this will be reset if you perform any read operations.
        Please store the value, if you need to retain the readCount.

        Returns:
            None: If no read has occurred.
            Integer: returns INTEGER value of rows that have been read.
        """
        return self.readCount

    def conflictsOccurred(self):
        """
        Returns:
            Boolean: True if a primary key collision occurred, otherwise,
                return False.
        """
        return self.conflictCount > 0

    def RemapValue(self, remapPool, SourceValue, MappingColumn, debug=False):
        """
        >>> import common
        >>> temp = common.BaseCsvFile("csvFile2.csv")
        >>> temp.setup_read()
        True
        >>> trans = {"Snake Wrangler":"Python!"}
        >>> for x in temp.readrow():
        ...     z = x
        ...
        >>> temp.remap_column(remapPool=trans, row=z, SourceColumn=" Title")
        'Python!'
        """
        #print(remapPool[SourceValue])
        if SourceValue in remapPool:
            try:
                NewValue = remapPool[SourceValue][MappingColumn].strip()
                # get the value
                if not(NewValue.strip() in ["", None]):
                    # if the value is not "" or None, return value
                    return NewValue
            except KeyError:
                print()
                print("%s is an invalid Column in the Remapping File" % MappingColumn)
                print()
                sys.exit(1)

        # org mrn was not found in pool,
        # *OR* the eMRN was in "", or None (Invalid value)
        return None


    def _read_by_key(self, key=None, restrictFields=None, clean_func=None, revealConflicts=False):
        """
        Args:
            key (string): Key is the column (of the header) to use as the key
                for the dictionary.  For data integrity the *KEY* must be
                unique. This is one-to-one.

            clean_func (func): If None, do not perform cleaning.  To Enable
                pass the function into the argument.

            restrictFields (list): This list contains the names (case-insensitive)
                of the columns to be gathered and stored in the data returned.
                (eg. If the database has Column1, Column2, Column3, Columnxx,
                    and you only want Column 3, restrictFields=["Column3"],
                    if you want column 1, 3, xx,
                        restrictFields=["Column1", "Column3", Columnxx"]

                        Mainly supplied to reduce memory consumption for larger
                        csv's.

        Returns:
            Dictionary: Dictionary of data from the extract.

        Raises:
            RuntimeError: Raises a RuntimeError if no key is specified.

        +---------+------------+-----------+
        | mrn     | first      | last      |
        +=========+============+===========+
        | 0123    | john       | doe       |
        +---------+------------+-----------+
        | 2124    | john       | gleason   |
        +---------+------------+-----------+
        | 3125    | jack       | hardy     |
        +---------+------------+-----------+
        | 4126    | frank      | franklin  |
        +---------+------------+-----------+
        | 5127    | peter      | griffin   |
        +---------+------------+-----------+
        | 6128    | thomas     | jane      |
        +---------+------------+-----------+

        .. code-block:

        test = _read_by_key(key="mrn")
        test.keys()
        dict_keys(['0123', '2134', '3125', '4126', '5127', 6128'])
        len(test.keys())
        6

        *NOTE* the key must be unique if the primary key is not unique, it will
         overwrite non-unique keys.  In that situation, only the last data
         written will be available.

        .. code-block:
        test = _read_by_key(key="first")
        test.keys()
        dict_keys(['JOHN', 'JACK', 'FRANK', 'PETER', 'THOMAS'])
        len(test.keys())
        5

        >>> test = BaseCsvFile(r"test_samples/monty.csv")
        >>> test.setup_read()
        True
        >>> data = test._read_by_key(key="value")
        >>> data.keys()
        dict_keys(['1', '2', '3'])

        >>> test = BaseCsvFile(r"test_samples/monty.csv")
        >>> test.setup_read()
        True
        >>> data = test._read_by_key(key="letter")
        >>> data.keys()
        dict_keys(['A', 'B', 'C'])

        >>> test = BaseCsvFile(r"test_samples/small.csv")
        >>> test.setup_read()
        True
        >>> data = test._read_by_key(key="2nd")
        >>> data.keys()
        dict_keys(['A', 'D', 'G'])

        >>> test = BaseCsvFile(r"test_samples/small.csv")
        >>> test.setup_read()
        True
        >>> data = test._read_by_key(key="4th")
        >>> data.keys()
        dict_keys(['C', 'F', 'I'])
        >>> data["F"]
        OrderedDict([('1st', '2'), ('2nd', 'd'), ('3rd', 'e'), ('4th', 'f')])
     """
        data = {}
        self.readCount = 0
        self.conflictCount = 0
        if key is None:
            raise RuntimeError("No key specified.")
        for row in self.csv_handler:
            if clean_func is not None:
                row = clean_func(row)

            keyvalue = str(row[key]).upper()
            if keyvalue in data:
                self.conflictCount += 1
                if revealConflicts:
                    print("Conflict: ", keyvalue)
            else:
                if restrictFields != None:
                    kvalues = list(row.keys())
                    for x in kvalues:
                        if x.title() not in restrictFields and x in row:
                            del(row[x])
                data[keyvalue] = row
                self.readCount += 1
        return data

    def _read_by_keys(self, keys=None, clean_func=None, revealConflicts=False):
        """
        Args:
            keys (string): Key is the column (of the header) to use as the key
                for the dictionary.  For data integrity the *KEY* must be
                unique. This is one-to-one.

            clean_func (func): If None, do not perform cleaning.  To Enable
                pass the function into the argument.

        Returns:
            Dictionary: Dictionary of data from the extract.

        Raises:
            RuntimeError: Raises a RuntimeError if no key is specified.

        +---------+------------+-----------+
        | mrn     | first      | last      |
        +=========+============+===========+
        | 0123    | john       | doe       |
        +---------+------------+-----------+
        | 2124    | john       | gleason   |
        +---------+------------+-----------+
        | 3125    | jack       | hardy     |
        +---------+------------+-----------+
        | 4126    | frank      | franklin  |
        +---------+------------+-----------+
        | 5127    | peter      | griffin   |
        +---------+------------+-----------+
        | 6128    | thomas     | jane      |
        +---------+------------+-----------+


    .. code-block:

        test = _read_by_keys(keys=["mrn"])
        test.keys()
        dict_keys(['0123', '2134', '3125', '4126', '5127', 6128'])
        len(test.keys())
        6

    *NOTE* the key must be unique if the primary key is not unique, it will
     overwrite non-unique keys.  Only the last data written will be
     available.

.. code-block:

        test = _read_by_keys(keys=["first", "last"])
        test.keys()
        dict_keys(['JOHN DOE', 'JOHN GLEASON', 'JACK HARDY', 'FRANK FRANKLIN',
         'PETER GRIFFIN', 'THOMAS JANE'])
        len(test.keys())
        6

        def clean(row):
            row["dob"] = row["dob"].replace("-", "")
            return row

        import common
        headers = ["first_name","last_name","mrn","dob","doc_date",\
                       "creation_date","urpath","filename","description",\
                       "doc_category","sha-512"]
        test = common.BaseCsvFile("test.csv", headers, headers)
        test.setup_read()
        True

        z = test._read_by_keys(keys=["first_name",\
                                         "last_name", "dob"], clean_func=clean)
        len(z)
        6
        z.keys()
        dict_keys(['ROSE_AAB_18901110', 'MARGARET_ABARE_19350917',\
                   'CARRIE_ABBOTT_19740118', 'GARY_ABBOTT_19520114',\
                   'HELEN_ABBOTT_19150831', 'JUDY_ABBOTT_19641009'])
        """
        data = {}
        self.readCount = 0
        self.conflictCount = 0
        if keys is None:
            raise RuntimeError("No key specified.")
        for row in self.csv_handler:
            keyvalue = []
            if clean_func is not None:
                row = clean_func(row)
            for key in keys:
                keyvalue.append(row[key].strip())
            keyvalue = '_'.join(keyvalue)
            if keyvalue in data:
                self.conflictCount += 1
                if revealConflicts:
                    print("Conflict: ", keyvalue)
            else:
                self.readCount += 1
                data[keyvalue.upper().strip()] = row
        return data

    read_by_key = _read_by_key
    read_by_keys = _read_by_keys
