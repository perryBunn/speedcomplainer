from csv_common import BaseCsvFile
from datetime import datetime
import os, os.path

"""
from rotating_csv import RotatingCsvFile, rotations
test = RotatingCsvFile(rotation=rotations["Rotate_Minute"], output_headers=["test", "test2"])
test.setup_write()
test.writerow(....)
# wait a minute
test.writerow(....)

"""

rotations = {'Rotate_Minute' : 0,
            'Rotate_Hour' : 1,
            'Rotate_Day' : 2,
#            'Rotate_Week' : 3,
#            'Rotate_Month' : 4,
#            'Rotate_Year' : 5
            }



class RotatingCsvFile(BaseCsvFile):
    def __init__(self,
                 rotation=rotations["Rotate_Day"],
                 output_headers=[], directory='',
                 suffix=""
                ):
        self.rotation_period = None
        self.directory = directory
        self.filename_template = None
        self.current_filename = self.set_rotation(rotation)
        self.headers = output_headers
        self.suffix = suffix
        BaseCsvFile.__init__(self,
                             fqpn=os.path.join(self.directory,
                                               "%s-%s.csv" % (self.current_filename,self.suffix)),
                             output_headers=output_headers)

    def set_rotation(self, rotation = None):
        self.rotation_period = rotation
        if self.rotation_period == rotations["Rotate_Minute"]:
            self.filename_template = "%Y-%m-%d %H_%M"
        elif self.rotation_period == rotations["Rotate_Hour"]:
            self.filename_template = "%Y-%m-%d %H"
        elif self.rotation_period == rotations["Rotate_Day"]:
            self.filename_template = "%Y-%m-%d"
        return datetime.strftime(datetime.now(), self.filename_template)

    def check_rotate(self):
        exceeded = False
        now = datetime.now()
        previous = datetime.strptime(self.current_filename, self.filename_template)
        duration = now-previous
        dur_in_sec = int(duration.total_seconds())
        if self.rotation_period == rotations["Rotate_Minute"]:
            exceeded = (dur_in_sec > 60)
        elif self.rotation_period == rotations["Rotate_Hour"]:
            exceeded = divmod(dur_in_sec, 3600)[0] >= 1
        elif self.rotation_period == rotations["Rotate_Day"]:
            exceeded = divmod(dur_in_sec, 86400)[0] >= 1
#        elif self.rotation == rotations["Rotate_Week"]:
 #           exceeded == divmod(duration_in_s, 86400*7)[0] >= 1
#        elif self.rotation == rotation["Rotate_Month"]:
#            exceeded == divmod(duration_in_s, 86400*7*4)[0] >= 1
#        elif self.rotation == rotation["Rotate_Year"]:
#            exceeded == divmod(duration_in_s, 86400*7*4*12)[0] >= 1
        if exceeded==True:
            self.close()
            self.__init__(rotation=self.rotation_period,
                          output_headers=self.output_headers,
                          directory=self.directory,
                          suffix=self.suffix)
            self.setup_write(writeheader=True)

    def writerow(self, datadict, clean=False):
        self.check_rotate()
        BaseCsvFile.writerow(self, datadict=datadict, clean=clean)
