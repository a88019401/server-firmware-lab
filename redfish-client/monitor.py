"""Small educational Redfish monitoring client for a local DMTF mock server."""

import os
import sys

import requests

BASE_URL = os.getenv("REDFISH_URL", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT_SECONDS = 5


def get_json(path):
    """Read one Redfish resource and return the decoded JSON dictionary."""
    if not path.startswith("/redfish/v1"):
        raise ValueError(f"Unexpected Redfish resource path: {path}")
    response = requests.get(
        BASE_URL + path,
        headers={"Accept": "application/json"},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def get_members(collection_path):
    """Follow the resource links in a Redfish collection."""
    collection = get_json(collection_path)
    return [get_json(item["@odata.id"]) for item in collection.get("Members", [])]


def status_text(resource):
    status = resource.get("Status") or {}
    return status.get("Health", "Unknown")


def report():
    print("=" * 48)
    print("        SERVER FIRMWARE LAB - REDFISH")
    print("=" * 48)
    print(f"Endpoint: {BASE_URL}\n")

    systems = get_members("/redfish/v1/Systems")
    managers = get_members("/redfish/v1/Managers")
    chassis_list = get_members("/redfish/v1/Chassis")

    print("[Systems]")
    for system in systems:
        print(" Name:", system.get("Name", "Unknown"))
        print(" Model:", system.get("Model", "Unknown"))
        print(" Power:", system.get("PowerState", "Unknown"))
        print(" Health:", status_text(system))

    print("\n[BMC Managers]")
    for manager in managers:
        print(" Name:", manager.get("Name", "Unknown"))
        print(" Firmware:", manager.get("FirmwareVersion", "Unknown"))
        print(" Health:", status_text(manager))

    print("\n[Chassis]")
    for chassis in chassis_list:
        print(" Name:", chassis.get("Name", "Unknown"))
        print(" Health:", status_text(chassis))
        power_uri = (chassis.get("Power") or {}).get("@odata.id")
        if power_uri:
            power = get_json(power_uri)
            for supply in power.get("PowerSupplies", []):
                name = supply.get("Name", "Power Supply")
                print(f" PSU ({name}) Health:", status_text(supply))


if __name__ == "__main__":
    try:
        report()
    except requests.exceptions.Timeout:
        print("ERROR: Redfish request timed out.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect. Is the DMTF mock server running on port 8000?", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as exc:
        print(f"ERROR: Server returned an HTTP error: {exc}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, KeyError) as exc:
        print(f"ERROR: Unexpected API data: {exc}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as exc:
        print(f"ERROR: Network request failed: {exc}", file=sys.stderr)
        sys.exit(1)
