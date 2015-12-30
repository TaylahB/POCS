import os
import shutil
import subprocess

from ..logger import get_logger
from .. import error
from .. import listify


class PanIndiDevice(object):

    """ Interface to INDI for controlling hardware devices

    Convenience methods are provided for interacting with devices.

    Args:
        name(str):      Name for the device
        driver(str):    INDI driver to load
    """

    def __init__(self, config={}, fifo='/tmp/pan_indiFIFO'):
        self.logger = get_logger(self)
        name = config.get('name', 'Generic PanIndiDevice')
        driver = config.get('driver', 'indi_simulator_ccd')
        port = config.get('port')

        self.logger.info('Creating device {} ({})'.format(name, driver))

        # Check the config for required items
        # assert config.get('port') is not None, self.logger.error(
        #     'No port specified, cannot create PanIndiDevice\n {}'.format(config))

        self._getprop = shutil.which('indi_getprop')
        self._setprop = shutil.which('indi_setprop')

        assert self._getprop is not None, error.PanError("Can't find indi_getprop")
        assert self._setprop is not None, error.PanError("Can't find indi_setprop")

        self.name = name
        self.driver = driver
        self.port = port

        self._fifo = fifo
        self._driver_loaded = False
        self._properties = {}

        self.config = config

        self.logger.debug("Loading driver for INDI mount")

        try:
            self._load_driver()
        except Exception as e:
            self.logger.warning("Couldn't load driver for device: {} {}".format(self.name, e))

##################################################################################################
# Properties
##################################################################################################

    @property
    def is_loaded(self):
        """ Tests if device driver is loaded on server. Catches the InvalidCommand error and returns False """
        try:
            self._driver_loaded = len(self.get_property()) > 0
        except error.FifoNotFound:
            self.logger.info("Fifo file not found. Unable to communicate with server.")
        except (AssertionError, error.InvalidCommand):
            self.logger.info("Device driver is not loaded. Unable to communicate with server.")

        return self._driver_loaded

    @property
    def is_connected(self):
        """ Tests if device is connected. """
        connected = False

        if self.is_loaded:
            try:
                if self.get_property('CONNECTION', 'CONNECT', result=True) == 'On':
                    connected = True
            except error.InvalidCommand:
                self.logger.debug("{} not connected".format(self.name))

        return connected

##################################################################################################
# Methods
##################################################################################################
    def get_all_properties(self):
        """ Gets all the properties for all the devices

        Returns:
            dict:   Key value pairs of all properties for all devices
        """
        for item in self.get_property('*'):
            name, val = item.split('=', maxsplit=1)
            dev, prop, elem = name.split('.')

            if prop in self._properties:
                self._properties[prop][elem] = val
            else:
                self._properties.setdefault(prop, {elem: val})

        return self._properties

    def get_property(self, property='*', element='*', result=False, verbose=False):
        """ Gets a property from a device

        Args:
            property(str):  Name of property. Defaults to '*'
            element(str):   Name of element. Defaults to '*'
            result(bool):   Parse response and return just result or output full
                response. Defaults to True (just the value).

        Returns:
            list(str) or str:      Output from the command. Either a list of lines or
                a single string.
        """
        assert os.path.exists(self._fifo), error.FifoNotFound("Can't get property")

        cmd = [self._getprop]
        if verbose:
            cmd.extend(['-vv'])
        if result:
            cmd.extend(['-1'])

        cmd.extend(['{}.{}.{}'.format(self.name, property, element)])

        output = ''
        try:
            output = subprocess.check_output(cmd, universal_newlines=True).strip().split('\n')
            if isinstance(output, int):
                if output > 0:
                    raise error.InvalidCommand("Problem with get_property. Output: {}".format(output))
        except subprocess.CalledProcessError as e:
            raise error.InvalidCommand("Can't send command to server. {} \t {}".format(e, output))
        except Exception as e:
            raise error.PanError(e)

        if not result:
            output = listify(output)
        else:
            output = output[0]

        return output

    def set_property(self, prop, elem_values, verbose=False):
        """ Sets a property from a device with a certain value

        Args:
            prop(str):              Name of property.
            elem_values(List[dict]):    List of (key, value) pairs for properties to set.
        """
        cmd = [self._setprop]
        if verbose:
            cmd.extend(['-vv'])

        self.logger.debug("elem_values: {}".format(elem_values))

        elems = ";".join(elem_values.keys())
        vals = ";".join(elem_values.values())

        cmd.extend(["{}.{}.{}={}".format(self.name, prop, elems, vals)])

        self.logger.debug("{} command: {}".format(self.name, cmd))

        output = ''
        try:
            output = subprocess.call(cmd)
            self.logger.debug("Output from set_property: {}".format(output))
            if output > 0:
                raise error.InvalidCommand("Problem with set_property. \n Cmd{} \n Output: {}".format(cmd, output))
        except subprocess.CalledProcessError as e:
            raise error.InvalidCommand(
                "Problem running indi command server. Does the server have valid drivers?")
        except Exception as e:
            raise error.InvalidCommand(e)

        return output

    def connect(self):
        """ Connect to device """
        self.logger.debug('Connecting {}'.format(self.name))

        if self.driver == 'indi_ieq_telescope':
            self.set_property('DEVICE_PORT', {'PORT': self.port})
        elif self.driver == 'indi_gphoto_ccd':
            self.set_property('SHUTTER_PORT', {'PORT': self.port})

        # Zero is success
        if self.set_property('CONNECTION', {'CONNECT': 'On'}) == 0:
            self.logger.debug('{} connected'.format(self.name))

            # Run through the initialization commands if present
            if self.config.get('init_commands'):
                self.logger.debug('Setting initial properties for {}'.format(self.name))

                for prop, elem in self.config.get('init_commands').items():
                    self.set_property(prop, elem)

            self.logger.debug('Getting properties for {}'.format(self.name))
        # self.get_all_properties()
        else:
            self.logger.warning("Can't connect to {}".format(self.name))

    def disconnect(self):
        """ Connect to device """
        self.logger.debug('Disconnecting {}'.format(self.name))
        self.set_property('CONNECTION', {'Disconnect': 'On'})

##################################################################################################
# Private Methods
##################################################################################################

    def _load_driver(self):
        """ Loads the driver for this client into the running server """

        if not self._driver_loaded:
            self.logger.debug("Loading driver for ".format(self.name))

            cmd = ['start', self.driver, '-n', '\"{}\"'.format(self.name)]

            self._write_to_fifo(cmd)

    def _unload_driver(self):
        """ Unloads the driver from the server """
        if self.is_loaded:
            self.logger.debug("Unloading driver".format(self.driver))

            # Need the explicit quotes below
            cmd = ['stop', self.driver, '\"{}\"'.format(self.name), '\n']

            self._write_to_fifo(cmd)

    def _write_to_fifo(self, cmd):
        """ Write the command to the FIFO server """
        assert self._fifo, error.InvalidCommand("No FIFO file found")

        str_cmd = ' '.join(cmd)
        self.logger.debug("Command to FIFO server: {}".format(str_cmd))
        try:
            self.logger.debug("Mount driver loaded10")
            # I can't seem to get the driver to load without the explicit flush and close
            with open(self._fifo, 'w') as f:
                self.logger.debug("Mount driver loaded1")
                f.write(str_cmd)
                self.logger.debug("Mount driver loaded2")
                f.flush()
                self.logger.debug("Mount driver loaded3")
                f.close()
        except Exception as e:
            raise error.PanError("Problem writing to FIFO: {}".format(e))
        else:
            self.logger.debug("Mount driver loaded")

        self.logger.debug("Mount driver loaded final")
