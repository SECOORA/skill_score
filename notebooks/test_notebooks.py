# -*- coding: utf-8 -*-
#
# test_notebooks.py
#
# purpose:
# author:   Filipe P. A. Fernandes
# e-mail:   ocefpaf@gmail
# web:      http://ocefpaf.github.io/
# created:  14-Aug-2014
# modified: Thu 14 Aug 2014 02:52:39 PM BRT
#
# obs:
#

import os
import sys
import nose
import unittest
from glob import glob


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
                execfile(py_file, {})
                sys.path.pop()
            else:
                print("Test for {} is not implemented!".format(py_file))

def main():
    unittest.main()


if __name__ == '__main__':
    main()
