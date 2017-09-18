#!/usr/bin/env python

# Select variables from a Colvars trajectory file and optionally plot them as
# a 1D graph as a function of time or of one of the variables.

# Source: https://github.com/colvars/colvars/blob/master/colvartools/plot_colvars_traj.py?raw=true

from __future__ import print_function

import os
import sys

if (sys.version_info < (2, 7)):
    # Save some explanations
    print("Python versions prior to 2.7 are no longer supported.")
    sys.exit(1)

import numpy as np


class Colvar_traj(object):
    """
    Class to store the trajectory of a collective variable.
    The series of step numbers are included, because collective 
    variables may be added or deleted during the simulation.
    """

    _name = ""
    _step = np.empty(shape=(0))
    _colvar = np.empty(shape=(0))

    def __init__(self, name):
        """Sets the name of the variable"""
        self._name = name
        self._step = np.zeros(shape=(0), dtype=np.int64)
        self._colvar = np.zeros(shape=(0), dtype=np.float)

    def __len__(self):
        """Returns the length of the trajectory"""
        return len(self._step)

    @property
    def num_dimensions(self):
        s = self._colvar.shape
        if (len(s) > 1):
            return s[1]
        else:
            return 1

    def set_num_dimensions(self, n_d):
        """Set the number of components of the collective variable"""
        if (len(self) > 0):
            print("Warning: changing the number of dimensions "
                  "of collective variable \""+self._name+
                  "\" after it has already been read.")
        if (n_d > 1):
            self._colvar.resize((len(self), n_d))
        else:
            self._colvar.resize((len(self)))

    def resize(self, n):
        """Change the number of records in the trajectory"""
        self._step.resize((n))
        if (len(self._colvar.shape) > 1):
            self._colvar.resize((n, self._colvar.shape[1]))
        else:
            self._colvar.resize((n))
            

    @property
    def name(self):
        """Returns the name of the collective variable"""
        return self._name
    @property
    def steps(self):
        """Returns the array of step numbers"""
        return self._step
    @property
    def values(self):
        """Returns the array of collective variable values"""
        return self._colvar


class Colvars_traj(object):
    """Trajectories of collective variables (read from colvars.traj file)"""

    _keys = []
    _start = {}
    _end = {}
    _colvars = {}
    _found = {}
    _count = -1
    _frame = -1

    def __init__(self):
        self._keys = ['step']
        self._start['step'] = 0
        self._end['step'] = -1
        self._count = 0
        self._frame = 0

    def __getitem__(self, key):
        return self._colvars[key]

    def __contains__(self, key):
        return key in self._colvars

    @property
    def num_frames_read(self):
        """Number of trajectory frames read so far"""
        return self._count

    @property
    def num_frames(self):
        """Number of trajectory frames processed"""
        return self._frame

    @property
    def variables(self):
        """Names of variables defined"""
        return self._keys[1:] # The first entry is "step"

    def parse_comment_line(self, line):
        """
        Read in a comment line from a colvars.traj file and update the names of
        collective variables if needed.
        """
        new_keys = (line[1:]).split() # skip the hash char
        if (not self._keys == ['step'] and self._colvars != {}):
            if (new_keys != self._keys):
                print("Info: Configuration changed; the new entries are: ")
                print(new_keys)
        self._keys = new_keys
        if (self._keys[0] != 'step'):
            raise KeyError("Error: file format incompatible with colvars.traj")
        # Find the boundaries of each column
        for i in range(1, len(self._keys)):
            self._start[self._keys[i]] = line.find(' '+self._keys[i])
            self._end[self._keys[i-1]] = line.find(' '+self._keys[i])
            self._end[self._keys[-1]] = -1

    def parse_line(self, line):
        """
        Read in a data line from a colvars.traj file
        only variables corresponding to the given keys are read
        """

        step = np.int64(line[0:self._end['step']])

        for v in self._keys[1:]:
            text = line[self._start[v]:self._end[v]]
            v_v = np.fromstring(text.lstrip(' (').rstrip(') '), sep=',')
            n_d = len(v_v)
            if (v not in self._colvars):
                self._colvars[v] = Colvar_traj(v)
                self._colvars[v].set_num_dimensions(n_d)
            cv = self._colvars[v]
            n = len(cv)
            cv.resize(n+1)
            cv.steps[n] = step
            cv.values[n] = v_v

        self._count += 1

    def read_files(self, filenames, list_variables=False,
                   first=0, last=-1, every=1):
        """
        Read a series of colvars.traj files.
        filenames : list of strings
            list of file names
        list_variables : bool
            list variable names to screen
        first : int
            index of first record to read in (see also mol load in VMD)
        last : int
            index of last record to read in
        every : int
            read every these many records
        """
        last = np.int64(last)
        if (last == -1):
            last = np.int64(np.iinfo(np.int64).max)
        for f in filenames:
            for line in f:
                if (len(line) == 0): continue
                if (line[:1] == "@"): continue # xmgr file metadata
                if (line[:1] == "#"):
                    self.parse_comment_line(line)
                    continue
                if (args.list_variables):
                    for v in self.variables:
                        print(v)
                    return
                if ((self._frame >= first) and (self._frame <= last) and 
                    (self._frame % every == 0)):
                    self.parse_line(line)
                self._frame += 1


if (__name__ == '__main__'):

    import argparse

    parser = \
        argparse.ArgumentParser(description='Select variables from a Colvars '
                                'trajectory file and optionally plot them '
                                'as a 1D graph as a function of time or of '
                                'one of the variables.', \
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(dest='filenames',
                        nargs='*',
                        type=argparse.FileType('r'),
                        help='Space-separated list of input files '
                        '(will be concatenated)',
                        default=[])

    parser.add_argument('--dt',
                        dest='dt',
                        type=float,
                        help='Integration time step',
                        default=2.0)

    parser.add_argument('--time-unit-shift',
                        dest='time_unit_shift',
                        type=int,
                        help='Divide time by 10 to this power.',
                        default=6)

    parser.add_argument('--first-frame',
                        dest='first',
                        type=np.int64,
                        help='First frame to read',
                        default=0)

    parser.add_argument('--last-frame',
                        dest='last',
                        type=np.int64,
                        help='Last frame to read',
                        default=-1)

    parser.add_argument('--skip-frames',
                        dest='skip',
                        type=np.int64,
                        help='Read every these many frames',
                        default=1)

    parser.add_argument('--variables',
                        dest='variables',
                        nargs='*',
                        type=str,
                        help='Space-separated list of names of collective '
                        'variables to write or plot.',
                        default=[])

    parser.add_argument('--list-variables',
                        dest='list_variables',
                        action='store_true',
                        help='List all names of collective variables '
                        'defined up until the first line of data.',
                        default=False)

    parser.add_argument('--output-file',
                        dest='output_file',
                        type=str,
                        help='Write the selected variables to a text file.  '
                        'The step number is always included as the first '
                        'column, and all variables '
                        'must be defined on the same trajectory segments.',
                        default=None)

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        matplotlib.rcParams['font.size'] = 10

        parser.add_argument('--plot',
                            dest='plot',
                            type=str,
                            help='Plot the variables in a PDF file '
                            'prefixed by this string.',
                            default=None)

        parser.add_argument('--plot-x-axis',
                            dest='plot_x_axis',
                            type=str,
                            help='Use this variable as X axis in the plot.',
                            default='time')

        parser.add_argument('--plot-x-label',
                            dest='plot_x_label',
                            type=str,
                            help='Use this label for the X axis.',
                            default=None)

        parser.add_argument('--plot-y-label',
                            dest='plot_y_label',
                            type=str,
                            help='Use this label for the Y axis.',
                            default=None)

        parser.add_argument('--plot-keys',
                            dest='plot_keys',
                            nargs='*',
                            type=str,
                            help='Alternative names for the legend',
                            default=[])

    except:
        pass

    args = parser.parse_args()

    if (len(args.filenames) == 0):
        raise Exception("No filenames provided.")

    colvars_traj = Colvars_traj()
    colvars_traj.read_files(args.filenames,
                            list_variables=args.list_variables,
                            first=args.first,
                            last=args.last,
                            every=args.skip)

    variables = args.variables
    if (len(variables) == 0): variables = colvars_traj.variables

    plot_keys = { var: var for var in variables }
    if (len(args.plot_keys)):
        if (len(args.plot_keys) != len(variables)):
            raise KeyError("--plot-keys must be as long "
                           "as the number of variables.")
        else:
            plot_keys = { var: key for (var, key) in zip(variables,
                                                         args.plot_keys) }

    time_unit = args.dt * np.power(10.0, -1*args.time_unit_shift)


    if (args.output_file):
        
        fmt = " %12d"
        columns = [colvars_traj[variables[0]].steps]
        for var in variables:
            cv = colvars_traj[var]
            for ic in range(cv.num_dimensions):
                y = cv.values
                if (cv.num_dimensions > 1):
                    y = cv.values[ic]
                columns += [y]
                fmt += " %21.14f"
        columns = tuple(columns)
        np.savetxt(fname=args.output_file,
                   X=list(zip(*columns)),
                   fmt=str(fmt))


    if (args.plot):

        lowercase = args.plot.lower()
        if (lowercase[-4:] == '.pdf'):
            args.plot = args.plot[:-4]

        pdf = PdfPages(args.plot+'.pdf')
        fig = plt.figure(figsize=(3.0, 3.0))
        if (args.plot_x_label): plt.xlabel(args.plot_x_label)
        if (args.plot_y_label): plt.ylabel(args.plot_y_label)

        for var in variables:

            cv = colvars_traj[var]

            x = cv.steps
            if (args.plot_x_axis == 'time'):
                x = cv.steps * time_unit
            elif (args.plot_x_axis == 'step'):
                x = cv.steps
            else:
                x = colvars_traj[args.plot_x_axis].values

            for ic in range(cv.num_dimensions):
                y = cv.values
                if (cv.num_dimensions > 1):
                    y = cv.values[ic]
                plt.plot(x, y, '-',
                         label=plot_keys[var],
                         alpha=0.5)
            
        plt.legend(loc='upper left')
        plt.tight_layout()

        pdf.savefig()
        pdf.close()

