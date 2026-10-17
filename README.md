# Server Firmware Lab — Redfish Monitoring Client

A beginner-friendly Python monitoring client for a **simulated** BMC Redfish API. It queries Systems, Managers, and Chassis, and reports status and firmware version. This is **not firmware** and does **not** monitor real hardware.

## Setup (Windows PowerShell)

Install Python 3.12, Git, and VS Code. Open PowerShell **in this directory**.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\redfish-client\requirements.txt

git clone https://github.com/DMTF/Redfish-Mockup-Server.git mockup-server
.\.venv\Scripts\python.exe -m pip install -r .\mockup-server\requirements.txt
```

## Terminal A — Start the mock server

```powershell
.\.venv\Scripts\python.exe .\mockup-server\redfishMockupServer.py -H 127.0.0.1 -p 8000 -D .\mockup-server\public-rackmount1 -S
```

The `-S` option is important: the DMTF built-in mockup is a *short-form* directory.

Visit http://127.0.0.1:8000/redfish/v1/Systems . Keep Terminal A running.

## Terminal B — Run monitoring client

```powershell
.\.venv\Scripts\python.exe .\redfish-client\monitor.py
```

## Run unit tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\redfish-client -p 'test_*.py' -v
```

## Try failure handling

```powershell
$env:REDFISH_URL='http://127.0.0.1:9999'
.\.venv\Scripts\python.exe .\redfish-client\monitor.py
Remove-Item Env:REDFISH_URL
```

This should show a connection error, proving the application handles a server that is unavailable.

## Architecture

`Python monitor.py` -> `HTTP GET /redfish/v1/...` -> `DMTF Redfish Mockup Server` -> `Sample JSON data`

DMTF source: https://github.com/DMTF/Redfish-Mockup-Server

## Future improvements

- Add CSV/JSON report output
- Add polling interval and health-change notifications
- Add authentication support for an actual secured BMC
- Add CI for tests
