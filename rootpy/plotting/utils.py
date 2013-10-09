# Copyright 2012 the rootpy developers
# distributed under the terms of the GNU General Public License
from __future__ import absolute_import

from math import log
import operator

import ROOT

from .hist import _Hist, HistStack
from .graph import _Graph1DBase, Graph

__all__ = [
    'get_limits',
    'get_band',
    'all_primitives',
    'canvases_with',
]

multiadd = lambda a, b: map(operator.add, a, b)
multisub = lambda a, b: map(operator.sub, a, b)


def _limits_helper(x1, x2, a, b, snap=False):
    """
    Given x1, x2, a, b, where:

        x1 - x0         x3 - x2
    a = ------- ,   b = -------
        x3 - x0         x3 - x0

    determine the points x0 and x3:

    x0         x1                x2       x3
    |----------|-----------------|--------|

    """
    if x2 < x1:
        raise ValueError("x2 < x1")
    if a + b >= 1:
        raise ValueError("a + b >= 1")
    if a < 0:
        raise ValueError("a < 0")
    if b < 0:
        raise ValueError("b < 0")
    if snap:
        if x1 >= 0:
            x1 = 0
            a = 0
        elif x2 <= 0:
            x2 = 0
            b = 0
        if x1 == x2 == 0:
            raise ValueError(
                "range is ambiguous when x1 == x2 == 0 and snap=True")
    elif x1 == x2:
        raise ValueError(
            "range is ambiguous when x1 == x2 and snap=False")
    if a == 0 and b == 0:
        return x1, x2
    elif a == 0:
        return x1, (x2 - b * x1) / (1 - b)
    elif b == 0:
        return (x1 - a * x2) / (1 - a), x2
    x0 = ((b / a) * x1 + x2 - (x2 - x1) / (1 - a - b)) / (1 + b / a)
    x3 = (x2 - x1) / (1 - a - b) + x0
    return x0, x3


def get_limits(plottables,
               xpadding=0,
               ypadding=0.1,
               xerror_in_padding=True,
               yerror_in_padding=True,
               snap=True,
               logx=False,
               logy=False,
               logx_crop_value=1E-5,
               logy_crop_value=1E-5,
               logx_base=10,
               logy_base=10):
    """
    Get the axes limits that should be used for a 1D histogram, graph, or stack
    of histograms.

    Parameters
    ----------

    plottables : Hist, Graph, HistStack, or list of such objects
        The object(s) for which visually pleasing plot boundaries are
        requested.

    xpadding : float or 2-tuple, optional (default=0)
        The horizontal padding as a fraction of the final plot width.

    ypadding : float or 2-tuple, optional (default=0.1)
        The vertical padding as a fraction of the final plot height.

    xerror_in_padding : bool, optional (default=True)
        If False then exclude the x error bars from the calculation of the plot
        width.

    yerror_in_padding : bool, optional (default=True)
        If False then exclude the y error bars from the calculation of the plot
        height.

    snap : bool, optional (default=True)
        Make the minimum or maximum of the vertical range the x-axis depending
        on if the plot maximum and minimum are above or below the x-axis. If
        the plot maximum is above the x-axis while the minimum is below the
        x-axis, then this option will have no effect.

    logx : bool, optional (default=False)
        If True, then the x-axis is log scale.

    logy : bool, optional (default=False)
        If True, then the y-axis is log scale.

    logx_crop_value : float, optional (default=1E-5)
        If an x-axis is using a logarithmic scale then crop all non-positive
        values with this value.

    logy_crop_value : float, optional (default=1E-5)
        If the y-axis is using a logarithmic scale then crop all non-positive
        values with this value.

    logx_base : float, optional (default=10)
        The base used for the logarithmic scale of the x-axis.

    logy_base : float, optional (default=10)
        The base used for the logarithmic scale of the y-axis.

    Returns
    -------

    xmin, xmax, ymin, ymax : tuple of plot boundaries
        The computed x and y-axis ranges.

    """
    try:
        import numpy as np
        use_numpy = True
    except ImportError:
        use_numpy = False

    if not isinstance(plottables, (list, tuple)):
        plottables = [plottables]

    xmin = float('+inf')
    xmax = float('-inf')
    ymin = float('+inf')
    ymax = float('-inf')

    for h in plottables:

        if isinstance(h, HistStack):
            h = h.sum

        if not isinstance(h, (_Hist, _Graph1DBase)):
            raise TypeError(
                "unable to determine plot axes ranges "
                "from object of type `{0}`".format(
                    type(h)))

        if use_numpy:
            y_array_min = y_array_max = np.array(list(h.y()))
            if yerror_in_padding:
                y_array_min = y_array_min - np.array(list(h.yerrl()))
                y_array_max = y_array_max + np.array(list(h.yerrh()))
            _ymin = y_array_min.min()
            _ymax = y_array_max.max()
        else:
            y_array_min = y_array_max = list(h.y())
            if yerror_in_padding:
                y_array_min = multisub(y_array_min, list(h.yerrl()))
                y_array_max = multiadd(y_array_max, list(h.yerrh()))
            _ymin = min(y_array_min)
            _ymax = max(y_array_max)

        if isinstance(h, _Graph1DBase):
            if use_numpy:
                x_array_min = x_array_max = np.array(list(h.x()))
                if xerror_in_padding:
                    x_array_min = x_array_min - np.array(list(h.xerrl()))
                    x_array_max = x_array_max + np.array(list(h.xerrh()))
                _xmin = x_array_min.min()
                _xmax = x_array_max.max()
            else:
                x_array_min = x_array_max = list(h.x())
                if xerror_in_padding:
                    x_array_min = multisub(x_array_min, list(h.xerrl()))
                    x_array_max = multiadd(x_array_max, list(h.xerrh()))
                _xmin = min(x_array_min)
                _xmax = max(x_array_max)
        else:
            _xmin = h.xedgesl(0)
            _xmax = h.xedgesh(-1)

        if logy:
            _ymin = max(logy_crop_value, _ymin)
            _ymax = max(logy_crop_value, _ymax)
        if logx:
            _xmin = max(logx_crop_value, _xmin)
            _xmax = max(logx_crop_value, _xmax)

        if _xmin < xmin:
            xmin = _xmin
        if _xmax > xmax:
            xmax = _xmax
        if _ymin < ymin:
            ymin = _ymin
        if _ymax > ymax:
            ymax = _ymax

    if isinstance(xpadding, (list, tuple)):
        if len(xpadding) != 2:
            raise ValueError("xpadding must be of length 2")
        xpadding_top = xpadding[0]
        xpadding_bottom = xpadding[1]
    else:
        xpadding_top = xpadding_bottom = xpadding

    if isinstance(ypadding, (list, tuple)):
        if len(ypadding) != 2:
            raise ValueError("ypadding must be of length 2")
        ypadding_top = ypadding[0]
        ypadding_bottom = ypadding[1]
    else:
        ypadding_top = ypadding_bottom = ypadding

    if logx:
        x0, x3 = _limits_helper(
            log(xmin, logx_base), log(xmax, logx_base),
            xpadding_bottom, xpadding_top)
        xmin = logx_base ** x0
        xmax = logx_base ** x3
    else:
        xmin, xmax = _limits_helper(
            xmin, xmax, xpadding_bottom, xpadding_top)

    if logy:
        y0, y3 = _limits_helper(
            log(ymin, logy_base), log(ymax, logy_base),
            ypadding_bottom, ypadding_top, snap=False)
        ymin = logy_base ** y0
        ymax = logy_base ** y3
    else:
        ymin, ymax = _limits_helper(
            ymin, ymax, ypadding_bottom, ypadding_top, snap=snap)

    return xmin, xmax, ymin, ymax


def get_band(low_hist, high_hist, middle_hist=None):
    """
    Convert the low and high histograms into a TGraphAsymmErrors centered at
    the middle histogram if not None otherwise the middle between the low and
    high points, to be used to draw a (possibly asymmetric) error band.
    """
    npoints = len(low_hist)
    band = Graph(npoints)
    for i in xrange(npoints):
        center = low_hist.x(i)
        width = low_hist.xwidth(i)
        low, high = low_hist[i], high_hist[i]
        if middle_hist is not None:
            middle = middle_hist[i]
        else:
            middle = (low + high) / 2.
        yerrh = max(high - middle, low - middle, 0)
        yerrl = abs(min(high - middle, low - middle, 0))
        band.SetPoint(i, center, middle)
        band.SetPointError(i, width / 2., width / 2.,
                           yerrl, yerrh)
    return band


def all_primitives(pad):
    """
    Recursively find all primities on a canvas, even those hiding behind a
    GetListOfFunctions() of a primitive
    """
    result = []
    for primitive in pad.GetListOfPrimitives():
        result.append(primitive)
        if hasattr(primitive, "GetListOfFunctions"):
            result.extend(primitive.GetListOfFunctions())
        if hasattr(primitive, "GetHistogram"):
            p = primitive.GetHistogram()
            if p:
                result.append(p)
        if isinstance(primitive, ROOT.TPad):
            result.extend(all_primitives(primitive))
    return result


def canvases_with(drawable):
    """
    Return a list of all canvases where `drawable` has been painted.

    Note: This function is inefficient because it inspects all objects on all
          canvases, recursively. Avoid calling it if you have a large number of
          canvases and primitives.
    """
    return [c for c in ROOT.gROOT.GetListOfCanvases()
            if drawable in all_primitives(c)]