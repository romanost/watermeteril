"""Water Meter IL sensor """
from datetime import timedelta
import logging
import re
from typing import Any, Callable, Dict, Optional
from urllib import parse
import requests
from bs4 import BeautifulSoup
import urllib.parse
from urllib.request import Request, urlopen
# import zlib
import gzip
import json

from aiohttp import ClientError
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
)

from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
import voluptuous as vol
import aiohttp
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
# Time between updating data from GitHub
SCAN_INTERVAL = timedelta(hours=3)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string
    }
)


def get_water_page (wuser:str, wpass:str):
    siteurl = "https://cp.city-mind.com/"
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'curl/7.68.0'}
    sdata = {}
    sdata['__EVENTTARGET'] = ""
    sdata['__EVENTARGUMENT'] = ""
    sdata['__LASTFOCUS'] = ""
    sdata['txtEmail'] = wuser
    sdata['txtPassword'] = wpass
    sdata['btnLogin'] = "כניסה"
    sdata['ddlWaterAuthority'] = ""
    sdata['txtConsumerNumber'] = ""
    sdata['txtPropertyNumber'] = ""
    sdata['txtRegistrationEmail'] = ""
    sdata['txtEmailValidation'] = ""

    try:
        s = Request(siteurl)
        # r = urlopen(s, None, 180).read()
        r = urlopen(s, None, 180).read()
        r = gzip.decompress(r)
        bs = BeautifulSoup(r, 'lxml')
        forms = bs.body.find('form').find_all('input', {"type": "hidden"})
        for i in forms:
            sdata[i['name']] = i['value']
        endata = urllib.parse.urlencode(sdata)
        qq = requests.post(siteurl, data=endata, headers=headers, allow_redirects=False)
        cookies = qq.cookies
        zz = requests.get("https://cp.city-mind.com/Default.aspx", cookies=cookies)
        bs = BeautifulSoup(zz.text, 'lxml')
        multi = bs.body.find('div', {"id": "div_meter_sn"}).findChild('span').text
        if not isinstance(multi, int):
            meturl = "https://cp.city-mind.com/App_API/Web/Meters.aspx?cmd=gl"
            metdata = "p=1"
            qq = requests.post(meturl, data=metdata, headers=headers, cookies=cookies)
            qq2 = json.loads(qq.text)
            qq3 = qq2["Response_Message"]["HTML"]
            bs2 = BeautifulSoup(qq3, 'lxml')
            meters = {}
            ths = []
            ri = -1
            for row in (bs2.find_all("tr")):
                th = row.findChildren("th")
                if th:
                    print(len(th))
                    for z in th:
                        ths.append(z.text)
                        # print(z)
                elif not row.findChildren("td", {"align": "center"}):
                    print("no th")
                    ri += 1
                    i = 0
                    meters[ri] = {}
                    for one in row.findChildren("td"):
                        print("ri:", ri, " i:", i, " ths:", ths[i])
                        meters[ri][ths[i]] = one.text
                        print(one)
                        i += 1
        i=0
        ms=[]
        for m in meters:
            ms.append(meters[m])

        if not bool(meters):
            data1 = json.loads(bs.body.find('div', {"id": "cphMain_div_properties"}).text)[0]
            data2 = json.loads(bs.body.find('div', {"id": "cphMain_div_monthly_consumption"}).text)[0]
            data1.update(data2)
            data1['מספר מונה']=multi
            data1['צריכה חודשית']=data1['Consumption']
            ms=[]
            ms.append(data1)


        return ms

    except:
        _LOGGER.exception("Error retrieving data water meter.")


async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the sensor platform."""
    session = async_get_clientsession(hass)
    wuser=config[CONF_USERNAME]
    wpass=config[CONF_PASSWORD]
    waterpage=await hass.async_add_executor_job(get_water_page,wuser, wpass)
    sensors = [WaterMeterILSensor(wuser, wpass, wmeter) for wmeter in waterpage]
    async_add_entities(sensors, update_before_add=True)


class WaterMeterILSensor(Entity):
    """Representation of a sensor."""

    def __init__(self, wuser: str, wpass: str, waterpage: Any):
        super().__init__()
        self._name="mone"
        self._state = None
        self._available = True
        self.attrs: Dict[str,Any]={}
        self.mone=0
        self.wpage=waterpage

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.mone

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def device_state_attributes(self) -> Dict[str, Any]:
        return self.attrs

    async def async_update(self):
        self.mone = self.wpage['מספר מונה']
        self.mone = self.wpage['מספר מונה']
        self._name=self.mone
        self.attrs=self.wpage
        self._state=self.wpage['צריכה חודשית']
        self.attrs['entity_id']='mone_'+str(self.mone)
        self.attrs['unique_id']='mone_'+self.mone
        self.attrs['friendly_name'] = 'mone_' + self.mone
        self._available=True
