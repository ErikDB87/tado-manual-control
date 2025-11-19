import argparse
# import datetime
from datetime import time
from datetime import datetime
from libtado.api import Tado
import os
from pyexcel_ods3 import save_data
from pyexcel_ods3 import get_data
from collections import OrderedDict
import webbrowser

############################################

### VARIABLES WHICH NEED TO BE SET ONCE: ###
# Set to 0 or 1. (0 = Celsius, 1 = Fahrenheit)
temperature_unit_choice = 0
# The path of the json file where the Tado refresh token is stored.
token_file_path = 'refresh_token.json'
# The directory in which you want to store the sheets.
sheets_dir = "schedule-sheets"

############################################


t = Tado(token_file_path=token_file_path)
temperature_units = ["celsius", "fahrenheit"]


def argparse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subcommands")

    # download_schedules:
    subparsers.add_parser(
        "download_schedules", help="Downloads the tado schedules to spreadsheets")

    # upload_schedules:
    subparsers.add_parser("upload_schedules", help="Uploads schedules from spreadsheets")

    # check_schedule_types:
    subparsers.add_parser(
        "check_schedule_types", help="Displays the active schedule type")

    # set_schedule_type:
    parse_set_schedule_type = subparsers.add_parser(
        "set_schedule_type", help="Sets the active schedule type (0 (= ONE_DAY), 1 (= THREE_DAY) or 2 (=SEVEN_DAY))")
    parse_set_schedule_type.add_argument(
        "-s", "--schedule_type", nargs=1, type=int, choices=[0, 1, 2])

    # manualtemp:
    parse_manualtemp = subparsers.add_parser(
        "manualtemp", help="Sets a defined zone to a define temperature")
    parse_manualtemp.add_argument("-z", "--zone", nargs=1, type=int)
    parse_manualtemp.add_argument("-t", "--temperature", nargs=1, type=float)

    # back_to_schedule:
    parse_back_to_schedule = subparsers.add_parser(
        "back_to_schedule", help="Reactivates the schedule for a defined zone")
    parse_back_to_schedule.add_argument("-z", "--zone", nargs=1, type=int)

    args = parser.parse_args()
    return args


def tadologin():
    status = t.get_device_activation_status()

    if status == "PENDING":
        url = t.get_device_verification_url()

        # to auto-open the browser (on a desktop device), un-comment the following line:
        webbrowser.open_new_tab(url)

        t.device_activation()

        status = t.get_device_activation_status()

    if status == "COMPLETED":
        print("Login successful")
    else:
        print(f"Login status is {status}")


def download_schedule_blocks_to_ods():
    zones = t.get_zones()

    for zone in zones:
        zone_id = zone["id"]
        zone_name = zone["name"]
        daytypes_with_schedule_blocks = []
        for schedule in range(3):
            schedule_blocks = t.get_schedule_blocks(zone_id, schedule)
            daytypes_with_schedule_blocks.append(schedule_blocks)

        outputforsheets = _output_for_sheets(daytypes_with_schedule_blocks)

        _output_to_sheets(zone_id, zone_name, outputforsheets)


def _output_for_sheets(daytypes_with_schedule_blocks):
    outputforsheets = {}

    for idx, block_list in enumerate(daytypes_with_schedule_blocks):
        for entry in block_list:
            start = entry["start"]
            end = entry["end"]
            temperature = entry["setting"]["temperature"][temperature_units[temperature_unit_choice]]
            topreservedata = [start, end, temperature]
            key = f"{idx}_{entry['dayType']}"
            if key not in outputforsheets:
                outputforsheets[key] = []
            outputforsheets[key].append(topreservedata)

    return outputforsheets


def _output_to_sheets(zone_id, zone_name, outputforsheets):
    os.makedirs(sheets_dir, exist_ok=True)

    filename = f"{zone_id} - {zone_name}.ods"
    filepath = os.path.join(sheets_dir, filename)
    data = OrderedDict()
    data.update(outputforsheets)
    save_data(filepath, data)


def _check_temperature(temp_to_check, column, sheet, file):
    if (not isinstance(temp_to_check, int)) and (not isinstance(temp_to_check, float)):
        error_message = 'The temperature "' + str(temp_to_check) + '" in column ' + str(column) + ' of sheet ' + \
            str(sheet) + 'in file ' + str(file) + ' isn\'t valid. Make sure to enter a number, using the proper decimal separator.'
        raise ValueError(error_message)
    else:
        return temp_to_check


def _check_times(time_to_check, column, sheet, file):
    if isinstance(time_to_check, time):
        time_to_check = time_to_check.strftime("%H:%M")
    elif isinstance(time_to_check, str):
        try:
            format = "%H:%M"
            bool(datetime.strptime(time_to_check, format))
        except ValueError:
            format = "%H:%M:%S"
            if datetime.strptime(time_to_check, format):
                time_to_check = time_to_check[:-3]
            else:
                error_message = 'The time "' + str(time_to_check) + '" in column ' + str(column) + ' of sheet ' + str(sheet) + 'in file ' + str(
                    file) + ' isn\'t valid. Make sure to enter a time, or a string formatted "%H:%M" (see https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes).'
                raise ValueError(error_message)
    else:
        error_message = 'The time "' + str(time_to_check) + '" in column ' + str(column) + ' of sheet ' + str(sheet) + 'in file ' + str(
            file) + ' isn\'t valid. Make sure to enter a time, or a string formatted "%H:%M" (see https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes).'
        raise ValueError(error_message)
    return time_to_check


def upload_schedule_blocks_from_ods():
    all_files = os.listdir(sheets_dir)
    for filename in all_files:
        if filename.endswith(".ods"):
            zone_int = int(filename.split(" - ")[0])
            filepath = os.path.join(sheets_dir, filename)
            sheets_from_ods_file = get_data(filepath)
            schedule_blocks_to_set = [
                [],
                [],
                []
            ]
            for key, value in sheets_from_ods_file.items():
                schedule = int(key[0])
                dayType = key[-(len(key)-2):]
                for entry in value:
                    start = _check_times(entry[0], "A", key, filename)
                    end = _check_times(entry[1], "B", key, filename)
                    temperature = _check_temperature(entry[2], "C", key, filename)
                    new_schedule_block = _new_schedule_block(
                        dayType, start, end, temperature)
                    schedule_blocks_to_set[schedule].append(new_schedule_block)

            for schedule_int, schedule_block in enumerate(schedule_blocks_to_set):
                t.set_schedule_blocks(zone_int, schedule_int, schedule_block)


def _new_schedule_block(dayType, start, end, temperature):
    new_schedule_block = {
        "dayType": dayType,
        "start": start,
        "end": end,
        "geolocationOverride": False,
        "setting": {
            "type": "HEATING",
            "power": "ON",
            "temperature": {
                temperature_units[temperature_unit_choice]: temperature
            }
        }
    }

    return new_schedule_block


def get_schedule_types():
    zones = t.get_zones()
    for zone in zones:
        schedule_type_object = t.get_schedule(zone["id"])
        verbose_string = "Zone " + \
            str(zone["id"])+" ("+zone["name"]+'): schedule type "' + \
            schedule_type_object["type"]+'"'
        print(verbose_string)


def set_schedule_types(schedule_type):
    schedule_types = [
        "ONE_DAY",
        "THREE_DAY",
        "SEVEN_DAY"
    ]
    output_text = "Schedule type: "+schedule_types[schedule_type]
    print(output_text)
    zones = t.get_zones()
    for zone in zones:
        t.set_schedule(zone["id"], schedule_type)


def set_zone_to_temp(zone, temperature):
    t.set_temperature(zone, temperature)


def reactivate_schedule(zone):
    t.end_manual_control(zone)


if __name__ == "__main__":
    args = argparse_args()
    tadologin()

    if args.subcommands == "download_schedules":
        print("Downloading your tado schedules to spreadsheets...")
        download_schedule_blocks_to_ods()
    elif args.subcommands == "upload_schedules":
        print("Uploading your tado schedules from spreadsheets...")
        upload_schedule_blocks_from_ods()
    elif args.subcommands == "check_schedule_types":
        print("Getting the schedule type for all your zones...")
        get_schedule_types()
    elif args.subcommands == "set_schedule_type":
        schedule_type = args.schedule_type[0]
        text = "Setting schedule type " + \
            str(schedule_type)+" for all your zones..."
        print(text)
        set_schedule_types(args.schedule_type[0])
    elif args.subcommands == "manualtemp":
        zone = args.zone[0]
        temp = args.temperature[0]
        if temperature_unit_choice == 0:
            text = "Setting temperature for zone " + str(zone) + " to " + str(temp) + " °C..."
        else:
            text = "Setting temperature for zone " + str(zone) + " to " + str(temp) + " °F..."
            temp = (temp - 32) * 5/9
        print(text)
        set_zone_to_temp(zone, temp)
    elif args.subcommands == "back_to_schedule":
        zone = args.zone[0]
        text = "Reactivating the schedule for zone "+str(zone)+"..."
        print(text)
        reactivate_schedule(zone)
