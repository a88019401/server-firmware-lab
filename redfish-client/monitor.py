"""Small educational Redfish monitoring client for a local DMTF mock server."""

import os
import sys
import time
from datetime import datetime

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


def needs_attention(health):
    return health in ("Warning", "Critical")


def summarize_health(health_list):
    # 四個計數器
    counts = {"OK": 0, "Warning": 0, "Critical": 0, "Unknown": 0}

    for health in health_list:
        if health in counts:
            counts[health] += 1
        else:
            counts["Unknown"] += 1

    if counts["Critical"] > 0:
        overall = "Critical"
    elif counts["Warning"] > 0:
        overall = "Warning"
    elif counts["Unknown"] > 0:
        overall = "Unknown"
    else:
        overall = "OK" if health_list else "Unknown"

    return counts, overall
def compare_health_snapshots(previous, current):
    changes = []

    for resource, new_health in current.items():
        if resource in previous:
            old_health = previous[resource]

            if old_health != new_health:
                changes.append(
                    (resource, old_health, new_health)
                )

    return changes
def monitor_loop(interval_seconds=10):
    print("Starting Redfish Auto Monitoring...")
    print(f"Polling interval: {interval_seconds} seconds")
    print("Press Ctrl+C to stop.\n")

    # 保存前一次的健康狀態
    previous_snapshot = None

    try:
        while True:
            check_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n[CHECK] {check_time}")

            # 取得這次健康報告及設備狀態
            current_snapshot = report()

            # 第一次查詢：沒有舊資料可以比較
            if previous_snapshot is None:
                print("[INFO] Initial snapshot saved.")

            else:
                # 比較前後兩次狀態
                changes = compare_health_snapshots(
                    previous_snapshot,
                    current_snapshot
                )

                if changes:
                    for resource, old_health, new_health in changes:

                        if needs_attention(new_health):
                            print(
                                f"[ALERT] {resource}: "
                                f"{old_health} -> {new_health}"
                            )

                        elif new_health == "OK":
                            print(
                                f"[RECOVERY] {resource}: "
                                f"{old_health} -> {new_health}"
                            )

                        else:
                            print(
                                f"[CHANGE] {resource}: "
                                f"{old_health} -> {new_health}"
                            )

                else:
                    print("[INFO] No health changes detected.")

            # 更新舊資料，提供下一輪比較
            previous_snapshot = current_snapshot

            print(f"\n[INFO] Waiting {interval_seconds} seconds...")
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n[INFO] Monitoring stopped by user.")

def report():
    print("=" * 48)
    print("        SERVER FIRMWARE LAB - REDFISH")
    print("=" * 48)
    print(f"Endpoint: {BASE_URL}\n")

    systems = get_members("/redfish/v1/Systems")
    managers = get_members("/redfish/v1/Managers")
    chassis_list = get_members("/redfish/v1/Chassis")
    # 空籃子，用來收集所有健康狀態
    health_list = []
    snapshot = {}
    print("[Systems]")
    for system in systems:
        print(" Name:", system.get("Name", "Unknown"))
        print(" Model:", system.get("Model", "Unknown"))
        print(" Power:", system.get("PowerState", "Unknown"))
        print(" Health:", status_text(system))

        # 收集 System 的健康狀態
        health_list.append(status_text(system))
        system_id = system.get("Id") or system.get("Name", "Unknown")
        snapshot[f"System:{system_id}"] = status_text(system)
    print("\n[BMC Managers]")
    for manager in managers:
        print(" Name:", manager.get("Name", "Unknown"))
        print(" Firmware:", manager.get("FirmwareVersion", "Unknown"))
        print(" Health:", status_text(manager))

        # 收集 Manager 的健康狀態
        health_list.append(status_text(manager))
        manager_id = manager.get("Id") or manager.get("Name", "Unknown")
        snapshot[f"Manager:{manager_id}"] = status_text(manager)

    print("\n[Chassis]")
    for chassis in chassis_list:
        print(" Name:", chassis.get("Name", "Unknown"))
        print(" Health:", status_text(chassis))

        # 收集 Chassis 的健康狀態
        health_list.append(status_text(chassis))
        chassis_id = chassis.get("Id") or chassis.get("Name", "Unknown")
        snapshot[f"Chassis:{chassis_id}"] = status_text(chassis)
        power_uri = (chassis.get("Power") or {}).get("@odata.id")
        if power_uri:
            power = get_json(power_uri)
            for supply in power.get("PowerSupplies", []):
                name = supply.get("Name", "Power Supply")
                health = status_text(supply)

                # 收集 Power Supply 的健康狀態
                health_list.append(health)
                snapshot[f"PSU:{chassis_id}:{name}"] = health
                print(f" PSU ({name}) Health:", health)
                # 如果設備的健康狀態是 Warning 或 Critical，就顯示一則異常警告。
                if needs_attention(health):
                    print(f" [ISSUE] {name} currently has health: {health}")
    counts, overall = summarize_health(health_list)
    print("\n" + "=" * 48)
    print("              SERVER HEALTH SUMMARY")
    print("=" * 48)

    print("Checked Resources :", len(health_list))
    print("Healthy (OK ^^)   :", counts["OK"])
    print("Warnings X(       :", counts["Warning"])
    print("Critical 0.0      :", counts["Critical"])
    print("Unknown ~.~       :", counts["Unknown"])
    print()
    print("Overall Health    :", overall.upper())
    return snapshot



    try:
        while True:
            # 1. 取得目前時間
            check_time = datetime.now().strftime("%H:%M:%S")

            # 2. 顯示這次查詢時間
            print(f"\n[CHECK] {check_time}")

            # 3. 執行原本的 Redfish 查詢
            report()

            # 4. 等待下一次查詢
            print(f"\n[INFO] Waiting {interval_seconds} seconds...")
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n[INFO] Monitoring stopped by user.")


if __name__ == "__main__":
    try:
        monitor_loop(interval_seconds=10)
    except requests.exceptions.Timeout:
        print("ERROR: Redfish request timed out.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(
            "ERROR: Cannot connect. Is the DMTF mock server running on port 8000?",
            file=sys.stderr,
        )
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
