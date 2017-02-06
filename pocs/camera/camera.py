from .. import PanBase

from ..utils import error
from ..utils import listify
from ..utils import load_module
from ..utils import images
from ..utils import current_time

from ..focuser.focuser import AbstractFocuser

from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.modeling import models, fitting

import numpy as np

import matplotlib.pyplot as plt

import re
import shutil
import subprocess
import yaml
import os

from threading import Event, Thread


class AbstractCamera(PanBase):

    """ Base class for all cameras """

    def __init__(self,
                 name='Generic Camera',
                 model='simulator',
                 port=None,
                 primary=False,
                 focuser=None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self._image_dir = self.config['directories']['images']
        except KeyError:
            self.logger.error("No images directory. Set image_dir in config")

        self.model = model
        self.port = port
        self.name = name

        self.is_primary = primary

        self._connected = False
        self._serial_number = 'XXXXXX'
        self._readout_time = kwargs.get('readout_time', 5.0)
        self._file_extension = kwargs.get('file_extension', 'fits')
        self.filter_type = 'RGGB'

        self.properties = None
        self._current_observation = None

        if focuser:
            if isinstance(focuser, AbstractFocuser):
                self.logger.debug("Focuser received: {}".format(focuser))
                self.focuser = focuser
                self.focuser.camera = self
            elif isinstance(focuser, dict):
                try:
                    module = load_module('pocs.focuser.{}'.format(focuser['model']))
                except AttributeError as err:
                    self.logger.critical("Couldn't import Focuser module {}!".format(module))
                    raise err
                else:
                    self.focuser = module.Focuser(**focuser, camera=self)
                    self.logger.debug("Focuser created: {}".format(self.focuser))
            else:
                # Should have been passed either a Focuser instance or a dict with Focuser
                # configuration. Got something else...
                self.logger.error("Expected either a Focuser instance or dict, got {}".format(focuser))
                self.focuser = None
        else:
            self.focuser = None

        self.logger.debug('Camera created: {}'.format(self))

##################################################################################################
# Properties
##################################################################################################

    @property
    def uid(self):
        """ A six-digit serial number for the camera """
        return self._serial_number[0:6]

    @property
    def is_connected(self):
        """ Is the camera available vai gphoto2 """
        return self._connected

    @property
    def readout_time(self):
        """ Readout time for the camera in seconds """
        return self._readout_time

    @property
    def file_extension(self):
        """ File extension for images saved by camera """
        return self._file_extension

    @property
    def CCD_temp(self):
        """
        Get current temperature of the camera's image sensor.

        Note: this only needs to be implemented for cameras which can provided this information,
        e.g. those with cooled image sensors.
        """
        raise NotImplementedError

    @property
    def CCD_set_point(self):
        """
        Get current value of the CCD set point, the target temperature for the camera's
        image sensor cooling control.

        Note: this only needs to be implemented for cameras which have cooled image sensors,
        not for those that don't (e.g. DSLRs).
        """
        raise NotImplementedError

    @CCD_set_point.setter
    def CCD_set_point(self, set_point):
        """
        Set value of the CCD set point, the target temperature for the camera's image sensor
        cooling control.

        Note: this only needs to be implemented for cameras which have cooled image sensors,
        not for those that don't (e.g. DSLRs).
        """
        raise NotImplementedError

    @property
    def CCD_cooling_enabled(self):
        """
        Get current status of the camera's image sensor cooling system (enabled/disabled).

        Note: this only needs to be implemented for cameras which have cooled image sensors,
        not for those that don't (e.g. DSLRs).
        """
        raise NotImplementedError

    @property
    def CCD_cooling_power(self):
        """
        Get current power level of the camera's image sensor cooling system (typically as
        a percentage of the maximum).

        Note: this only needs to be implemented for cameras which have cooled image sensors,
        not for those that don't (e.g. DSLRs).
        """
        raise NotImplementedError

##################################################################################################
# Methods
##################################################################################################

    def take_observation(self, *args, **kwargs):
        raise NotImplementedError

    def take_exposure(self, *args, **kwargs):
        raise NotImplementedError

    def process_exposure(self, *args, **kwargs):
        raise NotImplementedError

    def autofocus(self, coarse=False, blocking=False, *args, **kwargs):
        """
        Focuses the camera using the Vollath F4 merit function. Optionally performs a coarse focus first before
        performing the default fine focus. The expectation is that coarse focus will only be required for first use
        of a optic to establish the approximate position of infinity focus and after updating the intial focus
        position in the config only fine focus will be required.

        Args:
            coarse (bool, optional): Whether to begin with coarse focusing, default False
            blocking (bool, optional): Whether to block until autofocus complete, default False
            seconds (optional): Exposure time for focus exposures, if not specified will use value from config
            focus_range (2-tuple, optional): Coarse & fine focus sweep range, in encoder units. Specify to override 
                values from config
            focus_step (2-tuple, optional): Coarse & fine focus sweep steps, in encoder units. Specofy to override
                values from config
            thumbnail_size (optional): Size of square central region of image to use, default 500 x 500 pixels
            plots (bool, optional: Whether to write focus plots to images folder, default True.
        
        Returns:
            threading.Event: Event that will be set when autofocusing is complete
        """
        assert self.is_connected, self.logger.error("Camera must be connected for autofocus!")

        if coarse:
            coarse_event = Event()
            coarse_thread = Thread(target=self._autofocus,
                                   args=args,
                                   kwargs={'finished_event': coarse_event,
                                           'coarse': True,
                                           **kwargs})
            coarse_thread.start()
        else:
            coarse_event = None
        
        fine_event = Event()
        fine_thread = Thread(target=self._autofocus,
                             args=args,
                             kwargs={'start_event': coarse_event,
                                     'finished_event': fine_event,
                                     'coarse': False,
                                     **kwargs})
        fine_thread.start()

        if blocking:
            fine_event.wait()

        return fine_event
    
    def _autofocus(self, seconds=None, focus_range=None, focus_step=None,
                   coarse=False, thumbnail_size=750, plots=True,
                   start_event=None, finished_event=None, *args, **kwargs):
        # If passed a start_event wait until Event is set before proceeding (e.g. wait for coarse focus
        # to finish before starting fine focus).
        if start_event:
            start_event.wait()
        
        try:
            assert self.focuser.is_connected
        except AttributeError:
            self.logger.error('Attempted to autofocus but camera {} has no focuser!'.format(self))
            return
        except AssertionError:
            self.logger.error('Attempted to autofocus but camera {} focuser is not connected!'.format(self))
            return

        if not focus_range:
            if not self.focuser.autofocus_range:
                self.logger.error("No focus_range specified, aborting autofocus of {}!".format(self))
                return
            else:
                focus_range = self.focuser.autofocus_range

        if not focus_step:
            if not self.focuser.autofocus_step:
                self.logger.error("No focus_step specified, aborting autofocus of {}!".format(self))
                return
            else:
                focus_step = self.focuser.autofocus_step

        if not seconds:
            if not self.focuser.autofocus_seconds:
                self.logger.error("No focus exposure time specified, aborting autofocus of {}!".format(self))
                return
            else:
                seconds = self.focuser.autofocus_seconds

        initial_focus = self.focuser.position
        if coarse:
            self.logger.debug("Beginning coarse autofocus of {} - initial focus position: {}".format(self,
                                                                                                     initial_focus))
        else:
            self.logger.debug("Beginning autofocus of {} - initial focus position: {}".format(self, initial_focus))

        # Set up paths for temporary focus files, and plots if requested.
        image_dir = self.config['directories']['images']
        start_time = current_time(flatten=True)
        file_path = "{}/{}/{}/{}.{}".format(
            image_dir,
            'focus',
            self.uid,
            start_time,
            self.file_extension)

        if plots:
            # Take an image before focusing, grab a thumbnail from the centre and add it to the plot
            thumbnail = self._get_thumbnail(seconds, file_path, thumbnail_size)
            fig = plt.figure(figsize=(7, 18), tight_layout=True)
            ax1 = fig.add_subplot(3, 1, 1)
            im1 = ax1.imshow(thumbnail, interpolation='none', cmap='cubehelix')
            fig.colorbar(im1)
            ax1.set_title('Initial focus position: {}'.format(initial_focus))

        # Set up encoder positions for autofocus sweep, truncating at focus travel limits if required.
        if coarse:
            focus_range = focus_range[1]
            focus_step = focus_step[1]
        else:
            focus_range = focus_range[0]
            focus_step = focus_step[0]

        focus_positions = np.arange(max(initial_focus - focus_range / 2, self.focuser.min_position),
                                    min(initial_focus + focus_range / 2, self.focuser.max_position) + 1,
                                    focus_step, dtype=np.int)
        n_positions = len(focus_positions)

        f4 = np.empty((n_positions))

        for i, position in enumerate(focus_positions):
            # Move focus, updating focus_positions with actual encoder position after move.
            focus_positions[i] = self.focuser.move_to(position)

            # Take exposure
            thumbnail = self._get_thumbnail(seconds, file_path, thumbnail_size)

            # Calculate Vollath F4 focus metric for y axis direction. Using the Y axis to some extent
            # reduces the effects of periodic bias structure in these raw images as that that manifests
            # primarily as differences in bias level between columns rather than rows.
            f4[i] = images.vollath_F4(thumbnail, axis='Y')
            self.logger.debug("F4 at position {}: {}".format(position, f4[i]))

        # Find maximum values
        imax = f4.argmax()

        if imax == 0 or imax == (n_positions - 1):
            # TODO: have this automatically switch to coarse focus mode if this happens
            self.logger.warning("Best focus outside sweep range, aborting autofocus on {}!".format(self))
            best_focus = focus_positions[imax]

        elif not coarse:
            # Fit to data around the max value to determine best focus position. Lorentz function seems to fit OK
            # provided you only fit in the immediate vicinity of the max value.

            # Initialise models
            fit = models.Lorentz1D(x_0=focus_positions[imax], amplitude=f4.max()) + \
                                        models.Polynomial1D(degree=0, c0=0)

            # Initialise fitter
            fitter = fitting.LevMarLSQFitter()

            # Select data range for fitting. Tries to use 2 points either side of max, if in range.
            fitting_indices = (max(imax - 2, 0), min(imax + 2, n_positions - 1))

            # Fit models to data
            fit = fitter(fit,
                         focus_positions[fitting_indices[0]:fitting_indices[1] + 1],
                         f4[fitting_indices[0]:fitting_indices[1] + 1])

            best_focus = fit[0].x_0.value

        else:
            # Coarse focus, just use max value.
            best_focus = focus_positions[imax]

        if plots:
            ax2 = fig.add_subplot(3, 1, 2)
            ax2.plot(focus_positions, f4, 'bo', label='$F_4$')
            if not (imax == 0 or imax == (n_positions - 1)) and not coarse:
                fs = np.arange(focus_positions[fitting_indices[0]], focus_positions[fitting_indices[1]] + 1)
                ax2.plot(fs, fit(fs), 'b-', label='Lorentzian fit')

            ax2.set_xlim(focus_positions[0] - focus_step / 2, focus_positions[-1] + focus_step / 2)
            u_limit = 1.10 * f4.max()
            l_limit = min(0.95 * f4.min(), 1.05 * f4.min())
            ax2.set_ylim(l_limit, u_limit)
            ax2.vlines(initial_focus, l_limit, u_limit, colors='k', linestyles=':',
                       label='Initial focus')
            ax2.vlines(best_focus, l_limit, u_limit, colors='k', linestyles='--',
                       label='Best focus')
            ax2.set_xlabel('Focus position')
            ax2.set_ylabel('Vollath $F_4$')
            if coarse:
                ax2.set_title('{} coarse focus at {}'.format(self, start_time))
            else:
                ax2.set_title('{} fine focus at {}'.format(self, start_time))
            ax2.legend(loc='best')

        final_focus = self.focuser.move_to(best_focus)

        if plots:
            thumbnail = self._get_thumbnail(seconds, file_path, thumbnail_size)
            ax3 = fig.add_subplot(3, 1, 3)
            im3 = ax3.imshow(thumbnail, interpolation='none', cmap='cubehelix')
            fig.colorbar(im3)
            ax3.set_title('Final focus position: {}'.format(final_focus))
            plot_path = os.path.splitext(file_path)[0] + '.png'
            fig.savefig(plot_path)
            plt.close(fig)
            if coarse:
                self.logger.info('Coarse focus plot for camera {} written to {}'.format(self, plot_path))
            else:
                self.logger.info('Fine focus plot for camera {} written to {}'.format(self, plot_path))

        self.logger.debug('Autofocus of {} complete - final focus position: {}'.format(self, final_focus))

        if finished_event:
            finished_event.set()
        
        return initial_focus, final_focus

    def _get_thumbnail(self, seconds, file_path, thumbnail_size):
        """
        Takes an image, grabs the data, deletes the FITS file and
        returns a thumbnail from the centre of the iamge.
        """
        self.take_exposure(seconds, filename=file_path, blocking=True)
        image = fits.getdata(file_path)
        os.unlink(file_path)
        thumbnail = images.crop_data(image, box_width=thumbnail_size)
        return thumbnail

    def __str__(self):
        try:
            return "{} ({}) on {} with {} focuser".format(self.name, self.uid, self.port, self.focuser.name)
        except AttributeError:
            return "{} ({}) on {}".format(self.name, self.uid, self.port)


class AbstractGPhotoCamera(AbstractCamera):  # pragma: no cover

    """ Abstract camera class that uses gphoto2 interaction

    Args:
        config(Dict):   Config key/value pairs, defaults to empty dict.
    """

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)

        self._gphoto2 = shutil.which('gphoto2')
        assert self._gphoto2 is not None, error.PanError("Can't find gphoto2")

        self.logger.debug('GPhoto2 camera {} created on {}'.format(self.name, self.port))

        # Setup a holder for the process
        self._proc = None

    def command(self, cmd):
        """ Run gphoto2 command """

        # Test to see if there is a running command already
        if self._proc and self._proc.poll():
            raise error.InvalidCommand("Command already running")
        else:
            # Build the command.
            run_cmd = [self._gphoto2, '--port', self.port]
            run_cmd.extend(listify(cmd))

            self.logger.debug("gphoto2 command: {}".format(run_cmd))

            try:
                self._proc = subprocess.Popen(
                    run_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            except OSError as e:
                raise error.InvalidCommand("Can't send command to gphoto2. {} \t {}".format(e, run_cmd))
            except ValueError as e:
                raise error.InvalidCommand("Bad parameters to gphoto2. {} \t {}".format(e, run_cmd))
            except Exception as e:
                raise error.PanError(e)

    def get_command_result(self, timeout=10):
        """ Get the output from the command """

        self.logger.debug("Getting output from proc {}".format(self._proc.pid))

        try:
            outs, errs = self._proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.logger.debug("Timeout while waiting. Killing process {}".format(self._proc.pid))
            self._proc.kill()
            outs, errs = self._proc.communicate()

        self._proc = None

        return outs

    def wait_for_command(self, timeout=10):
        """ Wait for the given command to end

        This method merely waits for a subprocess to complete but doesn't attempt to communicate
        with the process (see `get_command_result` for that).
        """
        self.logger.debug("Waiting for proc {}".format(self._proc.pid))

        try:
            self._proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.logger.warning("Timeout expired for PID {}".format(self._proc.pid))

        self._proc = None

    def set_property(self, prop, val):
        """ Set a property on the camera """
        set_cmd = ['--set-config', '{}={}'.format(prop, val)]

        self.command(set_cmd)

        # Forces the command to wait
        self.get_command_result()

    def get_property(self, prop):
        """ Gets a property from the camera """
        set_cmd = ['--get-config', '{}'.format(prop)]

        self.command(set_cmd)
        result = self.get_command_result()

        output = ''
        for line in result.split('\n'):
            match = re.match('Current:\s(.*)', line)
            if match:
                output = match.group(1)

        return output

    def load_properties(self):
        ''' Load properties from the camera
        Reads all the configuration properties available via gphoto2 and populates
        a local list with these entries.
        '''
        self.logger.debug('Get All Properties')
        command = ['--list-all-config']

        self.properties = self.parse_config(self.command(command))

        if self.properties:
            self.logger.debug('  Found {} properties'.format(len(self.properties)))
        else:
            self.logger.warning('  Could not determine properties.')

    def parse_config(self, lines):
        yaml_string = ''
        for line in lines:
            IsID = len(line.split('/')) > 1
            IsLabel = re.match('^Label:\s(.*)', line)
            IsType = re.match('^Type:\s(.*)', line)
            IsCurrent = re.match('^Current:\s(.*)', line)
            IsChoice = re.match('^Choice:\s(\d+)\s(.*)', line)
            IsPrintable = re.match('^Printable:\s(.*)', line)
            IsHelp = re.match('^Help:\s(.*)', line)
            if IsLabel:
                line = '  {}'.format(line)
            elif IsType:
                line = '  {}'.format(line)
            elif IsCurrent:
                line = '  {}'.format(line)
            elif IsChoice:
                if int(IsChoice.group(1)) == 0:
                    line = '  Choices:\n    {}: {:d}'.format(IsChoice.group(2), int(IsChoice.group(1)))
                else:
                    line = '    {}: {:d}'.format(IsChoice.group(2), int(IsChoice.group(1)))
            elif IsPrintable:
                line = '  {}'.format(line)
            elif IsHelp:
                line = '  {}'.format(line)
            elif IsID:
                line = '- ID: {}'.format(line)
            elif line == '':
                continue
            else:
                print('Line Not Parsed: {}'.format(line))
            yaml_string += '{}\n'.format(line)
        properties_list = yaml.load(yaml_string)
        if isinstance(properties_list, list):
            properties = {}
            for property in properties_list:
                if property['Label']:
                    properties[property['Label']] = property
        else:
            properties = properties_list
        return properties
