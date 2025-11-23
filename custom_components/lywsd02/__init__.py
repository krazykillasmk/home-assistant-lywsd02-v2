from __future__ import annotations
import time
import struct
import logging
from datetime import datetime
from bleak import BleakClient
from bleak_retry_connector import establish_connection
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.components import bluetooth

DOMAIN = "lywsd02"
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)  # Wymuszenie poziomu INFO

_UUID_TIME = 'EBE0CCB7-7A0A-4B0C-8A1A-6FF2997DA3A6'
_UUID_TEMO = 'EBE0CCBE-7A0A-4B0C-8A1A-6FF2997DA3A6'

def get_localized_timestamp():
    now = int(time.time())
    utc = datetime.utcfromtimestamp(now)
    local = datetime.fromtimestamp(now)
    diff = (utc-local).seconds
    return now - diff

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """
    Based off https://github.com/h4/lywsd02
    """
    
    @callback
    async def set_time(call: ServiceCall) -> None:
        mac = call.data['mac'].upper()
        if not mac:
            _LOGGER.error(f"The 'mac' parameter is missing from service call: {call.data}.")
            return
        
        tz_offset = call.data.get('tz_offset', 0)
        
        ble_device = bluetooth.async_ble_device_from_address(
            hass,
            mac,
            connectable=True
        )
        
        if not ble_device:
            _LOGGER.error(f"Could not find '{mac}'.")
            return
        
        _LOGGER.info(f"Found '{ble_device}' - Attempting to update time.")
        
        temo_set = False
        ckmo_set = False
        
        temo = call.data.get('temp_mode', '') or "x"
        temo = temo.upper()
        _LOGGER.debug(f"temo var: {temo}")
        
        if temo in 'CF':
            data_temp_mode = struct.pack('B', (0x01 if temo == 'F' else 0xFF))
            _LOGGER.debug(f"Will set temp_mode")
            temo_set = True
        
        ckmo = call.data.get('clock_mode', 0)
        _LOGGER.debug(f"ckmo var: {ckmo}")
        
        if ckmo in [12, 24]:
            data_clock_mode = struct.pack('IHB', 0, 0, 0xaa if ckmo == 12 else 0x00)
            _LOGGER.debug(f"Will set clock_mode")
            ckmo_set = True
        
        tout = int(call.data.get('timeout', 60))
        
        # Użycie establish_connection zamiast BleakClient bezpośrednio
        client = await establish_connection(
            BleakClient,
            ble_device,
            mac,
            timeout=tout
        )
        
        try:
            timestamp = int(
                call.data.get('timestamp') or get_localized_timestamp()
            )
            data = struct.pack('Ib', timestamp, tz_offset)
            
            _LOGGER.info(f"Writing time to '{mac}'...")
            await client.write_gatt_char(_UUID_TIME, data)
            _LOGGER.info(f"✓ Time successfully written to '{mac}'")
            
            if temo_set:
                _LOGGER.info(f"Writing temperature mode '{temo}' to '{mac}'...")
                await client.write_gatt_char(_UUID_TEMO, data_temp_mode)
                _LOGGER.info(f"✓ Temperature mode successfully set to '{temo}'")
            
            if ckmo_set:
                _LOGGER.info(f"Writing clock mode '{ckmo}h' to '{mac}'...")
                await client.write_gatt_char(_UUID_TIME, data_clock_mode)
                _LOGGER.info(f"✓ Clock mode successfully set to '{ckmo}h'")
            
            _LOGGER.info(f"✓ SUCCESS - All operations completed for '{mac}' (timestamp: {timestamp}, tz_offset: {tz_offset}h)")
            
            # Dodaj notyfikację w interfejsie Home Assistant
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": f"Czas zsynchronizowany pomyślnie!\nMAC: {mac}\nTimestamp: {timestamp}\nOffset: {tz_offset}h",
                    "title": "LYWSD02 - Sukces",
                    "notification_id": f"lywsd02_{mac}"
                }
            )
            
        except Exception as e:
            _LOGGER.error(f"✗ FAILED - Error writing to '{mac}': {type(e).__name__}: {e}")
            
            # Dodaj notyfikację o błędzie
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": f"Błąd synchronizacji czasu!\nMAC: {mac}\nBłąd: {type(e).__name__}: {e}",
                    "title": "LYWSD02 - Błąd",
                    "notification_id": f"lywsd02_{mac}_error"
                }
            )
            raise
        finally:
            try:
                await client.disconnect()
                _LOGGER.debug(f"Disconnected from '{mac}'")
            except Exception as e:
                _LOGGER.warning(f"Error during disconnect from '{mac}': {e}")
    
    hass.services.async_register(DOMAIN, 'set_time', set_time)
    return True
