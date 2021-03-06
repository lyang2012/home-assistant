"""
Support for Fast.com internet speed testing sensor.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.fastdotcom/
"""
import asyncio
import logging
import voluptuous as vol

import homeassistant.util.dt as dt_util
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (DOMAIN, PLATFORM_SCHEMA)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import track_time_change
from homeassistant.helpers.restore_state import async_get_last_state

REQUIREMENTS = ['fastdotcom==0.0.1']

_LOGGER = logging.getLogger(__name__)

CONF_SECOND = 'second'
CONF_MINUTE = 'minute'
CONF_HOUR = 'hour'
CONF_DAY = 'day'
CONF_MANUAL = 'manual'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SECOND, default=[0]):
        vol.All(cv.ensure_list, [vol.All(vol.Coerce(int), vol.Range(0, 59))]),
    vol.Optional(CONF_MINUTE, default=[0]):
        vol.All(cv.ensure_list, [vol.All(vol.Coerce(int), vol.Range(0, 59))]),
    vol.Optional(CONF_HOUR):
        vol.All(cv.ensure_list, [vol.All(vol.Coerce(int), vol.Range(0, 23))]),
    vol.Optional(CONF_DAY):
        vol.All(cv.ensure_list, [vol.All(vol.Coerce(int), vol.Range(1, 31))]),
    vol.Optional(CONF_MANUAL, default=False): cv.boolean,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Fast.com sensor."""
    data = SpeedtestData(hass, config)
    sensor = SpeedtestSensor(data)
    add_devices([sensor])

    def update(call=None):
        """Update service for manual updates."""
        data.update(dt_util.now())
        sensor.update()

    hass.services.register(DOMAIN, 'update_fastdotcom', update)


class SpeedtestSensor(Entity):
    """Implementation of a FAst.com sensor."""

    def __init__(self, speedtest_data):
        """Initialize the sensor."""
        self._name = 'Fast.com Download'
        self.speedtest_client = speedtest_data
        self._state = None
        self._unit_of_measurement = 'Mbit/s'

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    def update(self):
        """Get the latest data and update the states."""
        data = self.speedtest_client.data
        if data is None:
            return

        self._state = data['download']

    @asyncio.coroutine
    def async_added_to_hass(self):
        """Called when entity is about to be added to hass."""
        state = yield from async_get_last_state(self.hass, self.entity_id)
        if not state:
            return
        self._state = state.state


class SpeedtestData(object):
    """Get the latest data from fast.com."""

    def __init__(self, hass, config):
        """Initialize the data object."""
        self.data = None
        if not config.get(CONF_MANUAL):
            track_time_change(hass, self.update,
                              second=config.get(CONF_SECOND),
                              minute=config.get(CONF_MINUTE),
                              hour=config.get(CONF_HOUR),
                              day=config.get(CONF_DAY))

    def update(self, now):
        """Get the latest data from fast.com."""
        from fastdotcom import fast_com
        _LOGGER.info('Executing fast.com speedtest')
        self.data = {'download': fast_com()}
