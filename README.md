# tado-manual-control
Using tado's API to easily make heating schedules, to set TVR's to `MANUAL` or to set them back to `SCHEDULE`

## Goal
It annoyed me that the only way to change tado schedules, is to add/edit every block manually in the mobile or web app. I wanted something more manageable.

I finally went with an approach that creates an `ods` file per zone, and in that zone, a sheet per day within the schedule type (so `0_MONDAY_TO_SUNDAY`, `1_MONDAY_TO_FRIDAY`, `1_SATURDAY`, `1_SUNDAY`, `2_MONDAY`, `2_TUESDAY` etc.).

Within each sheet the setup is very basic: in column A is the begin hour of the schedule block, in column B the end hour, and in column C the temperature. The first begin hour and the last end hour must always be `00:00`.

While I was working on this script, tado announced it would limit API calls to 100 per day. Out of necessity, I decided to add limited TVR control.

## Features
### Download schedules
The script can download all schedules to above mentioned `ods` files.

### Upload schedules
It can also upload from these files (after you've made manual changes).

### Check schedule type
There's also the possibility to check whether schedule type all zones are in (`ONE_DAY`, `THREE_DAY` or `SEVEN_DAY`).

### Set schedule type
You can also set all zones to the same schedule type. I didn't provide a per-zone solution, but it's easy to implement it yourself, of course.

### Set the temperature for a specific zone
Because the openHAB tado binding became unusable due to tado's API call limit, I added the function to set the temperature for a specific zone.

### Reactivate schedule mode for a specific zone
Logically, I also added a way to reactivate the schedule for a specific zone.

## Requirements
Obviously, the file `requirements.txt` contains requirements.

I altered `/libtado/api.py` to take advantage of a workaround for tado's API limit ( https://github.com/s1adem4n/tado-api-proxy). I amended line 125, and added a line 126:
```
# api = 'https://my.tado.com/api/v2'             ## This was the original URL
api = 'http://192.168.1.10:52069/api/v2'         ## This works, thanks to https://github.com/s1adem4n/tado-api-proxy
```

## Settings
The script doesn't require much personalization, except for three variables (which are already set to a default):
```
* temperature_unit_choice = 0              # Set to 0 or 1. (0 = Celsius, 1 = Fahrenheit)
* token_file_path = 'refresh_token.json'   # The path of the json file where the Tado refresh token is stored.
* sheets_dir = "schedule-sheets"           # The directory in which you want to store the sheets.
```

If you're using the script in openHAB (https://community.openhab.org/t/very-partial-tado-binding-alternative/166355), make sure to use the **absolute** path for `token_file_path` (e.g. `'/var/lib/openhab/bin/python/tado-manual-control/refresh_token.json'`). Otherwise the script might not find it.

## API calls
I started working on this before tado came up with its idiotic idea to limit API calls to 100 per day. But I was almost done, so I finished it anyway. The script makes API calls:
* `download_schedules`: 1 call to get all your zones, then 3 calls per zone
* `upload_schedules`: 3 calls per zone
* `check_schedule_types`: 1 call to get all your zones, then 1 call per zone
* `set_schedule_type`: 1 call to get all your zones, then 1 call per zone
* `manualtemp`: 1 call
* `back_to_schedule`: 1 call

## Acknowledgements
Guided by an article I found online (https://samharrison.science/posts/tado-heating-python-api/), I found two python libraries which used the unofficial tado API (https://kritsel.github.io/tado-openapispec-v2/swagger):
* python-tado (https://pypi.org/project/python-tado/) - I ran into an issue, which I couldn't resolve quickly. The problem was probably on my end, but I moved on...
* libtado (https://libtado.readthedocs.io/en/latest/) - This is the library I ended up using, although I did need to fix something (see above). At the time of my latest commit (22/11/2025), the most recent version of `libtado` was `4.1.1`.

I'm sure both libraries have value, and both deserve being honored.

Also s1adem4n deserves credit for his workaround around tado's API limit: https://github.com/s1adem4n/tado-api-proxy.

## Possible enhancements
I haven't done a lot of alpha testing, so any suggestions are welcome!