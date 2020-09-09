# Water meter IL #

Used to read water data from cp.city-mind.com

Before using open an account on [cp.city-mind.com](https://cp.city-mind.com/)

### Installation using HACS

1. Add `https://github.com/romanost/watermeteril` as a custom repository
2. Click install under "Water meter IL"
3. Configure the integration and restart the Home Assistant


### Manual Installation

1. Download `watermeteril.zip`
2. Unpack and copy the `custom_components/watermeteril` folder into 
   the `custom_components` folder directory of your Home Assistant.
3. Configure the integration and restart the Home Assistant


### Configuration
```yaml
sensor:
  - platform: watermeteril
    username: username
    password: password
```
