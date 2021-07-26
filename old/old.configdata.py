"""
:Module: Config
:Date: 2015-05-1
:Platforms: Mac, Windows, Unix (Tested under Mac OS X)
:Version: 1
:Authors:
    - Benjamin Schollnick

:Description:
    This module will read in the configuration ini.

**Modules Used (Batteries Included)**:

   * os
   * os.path
   * stat
   * string
   * time

:Concept:

    While not ideal, INI based configuration files, are easy to debug,
    and more important, easy to update.

    The module is passed the location of the configuration files,
    and will read in the necessary ini files (settings.ini by default).
    The different segments of the ini file will be stored in a seperate
    dictionary for ease of use..

code::

    load_config_data()
    print(USER)
    print(EMAIL)

"""
#####################################################
#   Batteries Included imports
import ConfigParser
import os
import os.path

#####################################################
#   3rd party imports
#
#   None

CONFIGURATION = {}


def try_int(value):
    """
    Try to convert value into an integer, and ignore any exceptions.
    If fails, just return the un-altered value.
    """
    try:
        return int(value.strip())
    except:
        return value


def load_data(filename=None, ini_group=""):
    """
:Description:
    Load data from the ini file

Args:

    filename: (default value = None) To override the filename
        pass a string containing the new filename.

    oname: The option name to read from the ini

 Returns:
    loaded dictionary

code::

    USER = load_user_data(settings_file)
    EMAIL = load_email_data(settings_file)

    """
    if filename is None:
        filename = "settings.ini"
    data = {}
    try:
        config = ConfigParser.SafeConfigParser()
        config.read(os.path.join(os.getcwd(), filename))
        for option_name in config.options(ini_group.strip()):
            data[option_name] = try_int(config.get(ini_group, option_name))
    except ConfigParser.NoSectionError:
        pass
    return data


def load_config_data(settings_file=None, sections=()):
    """
Args:

    filename : string
        (default value = None) To override the filename
        pass a string containing the new filename.

Returns:
    dictionary
        email dictionary
    dictionary
        user dictionary


code::

    load_config_data()
    print USER
    print EMAIL

    """
    for section_name in sections:
        CONFIGURATION[section_name] = load_data(settings_file, section_name)
        if CONFIGURATION[section_name] == {}:
            print("* INI file does not contain any data for section (%s)." %\
                section_name)


if __name__ == "__main__":
    load_config_data(sections=("NYSIIS_USER", "EMAIL", "NYSIIS", "CONFLUENCE"))
    print( CONFIGURATION.keys())
    print("User - %s\n" % CONFIGURATION["NYSIIS_USER"])
    print("Email - %s\n" % CONFIGURATION["EMAIL"])
    print("NYSIIS - %s\n" % CONFIGURATION["NYSIIS"])
    print("CONFLUENCE - %s\n" % CONFIGURATION["CONFLUENCE"])
