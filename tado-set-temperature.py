import argparse
from libtado.api import Tado
import webbrowser

############################################

### VARIABLES WHICH NEED TO BE SET ONCE: ###

# The path of the json file where the Tado refresh token is stored.
token_file_path = 'refresh_token.json'

# The temperature can only be set in Celsius, because that is wat libtado's API expects.
# If you want to integrate Farenheit, change the API, or integrate a calculation function.
# The below variable is therefore pointless:
# Set to 0 or 1. (0 = Celsius, 1 = Fahrenheit)
# temperature_unit_choice = 0

############################################


t = Tado(token_file_path=token_file_path)


# This variable is also pointless - see above.
# temperature_units = ["celsius", "fahrenheit"]


def argparse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--targettemp", nargs=1,
                        help="Enter the desired temperature", type=float, required=True)
    parser.add_argument("-z", "--zone", nargs=1,
                        help="Enter zone number", type=int, required=True)
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


def set_temperature(zone, temperature):
    t.set_temperature(zone, temperature)


if __name__ == "__main__":
    args = argparse_args()
    tadologin()

    set_temperature(args.zone[0], args.targettemp[0])
    # set_temperature(2, 11.5)
