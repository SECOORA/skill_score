# -*- coding: utf-8 -*-
#
# skill_score.py
#
# purpose:  Skill score functions
# author:   Filipe P. A. Fernandes
# e-mail:   ocefpaf@gmail
# web:      http://ocefpaf.github.io/
# created:  05-Feb-2015
# modified: Thu 05 Feb 2015 04:26:47 PM BRT
#
# obs:
#

# TODO: Taylor, SST

import numpy as np
from scipy.stats.stats import pearsonr

__all__ = ['both_valid']


def both_valid(x, y):
    """Returns a mask where both series are valid."""
    mask_x = np.isnan(x)
    mask_y = np.isnan(y)
    return np.logical_and(~mask_x, ~mask_y)


def pearsonr_paired(x, y):
    mask = both_valid(x, y)
    r, p = pearsonr(x[mask]-x.mean(), y[mask]-y.mean())
    return r, p
