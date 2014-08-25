# -*- coding: utf-8 -*-
#
# test_notebooks.py
#
# purpose:  Run all notebooks, compare the results and report Exceptions.
# author:   Filipe P. A. Fernandes
# e-mail:   ocefpaf@gmail
# web:      http://ocefpaf.github.io/
# created:  14-Aug-2014
# modified: Mon 25 Aug 2014 11:49:10 AM BRT
#
# obs:
#

import os
import sys
import unittest
import subprocess
from glob import glob


def clean_output(pattern='*.nc'):
    [os.unlink(fname) for fname in glob(pattern)]


class RunNotebooks(unittest.TestCase):
    def setUp(self):
        files = []
        for root, dirs, fnames in os.walk(os.getcwd()):
            for fname in fnames:
                if fname.endswith(".py"):
                    files.append(os.path.join(root, fname))
        self.files = files

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def test_notebooks(self):
        """Test the .py version of the .ipynb."""
        for fname in self.files:
            folder, py_file = os.path.split(fname)
            if 'utilities.py' in py_file:
                pass
            elif 'inundation_secoora' in fname:
                os.chdir(folder)  # If reading or saving in that directory.
                sys.path.append(folder)
                print("Running {}".format(py_file))
                clean_output(pattern='*.nc')
                clean_output(pattern='*.log')
                clean_output(pattern='*.json')
                subprocess.call(['python', py_file])
                sys.path.pop()
            else:
                print("Test for {} is not implemented!".format(py_file))


def main():
    unittest.main()


if __name__ == '__main__':
    main()
