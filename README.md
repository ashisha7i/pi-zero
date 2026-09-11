## The Pi-peline

Simple tasks/pipeline app. Hosted on Raspberry Pi Zero W (as of September 2026).


---
### Deployment

- Copy files to the RPi `/home/admin/pi-list' directory
- Restart the application (see section below)

---

### Configuration / Commands (on RaspberryPi Zero)


- `systemd` service configured at `/etc/systemd/system/flask-app.service`.

  ```text
  [Unit]
  Description=Pi-List Application
  After=network.target tailscaled.service

  [Service]
  User=admin
  WorkingDirectory=/home/admin/pi-list/
  ExecStart=/usr/bin/python3 /home/admin/pi-list/app.py
  Restart=always
  RestartSec=10

  [Install]
  WantedBy=multi-user.target
  ```
  
- `tailscale` used to expose the application to restricted users on the internet.

### Manage service
Use the following commands to manage the state of the service

```shell
sudo systemctl start pi-list.service      # start it now
sudo systemctl stop pi-list.service       # stop it now
sudo systemctl restart pi-list.service    # stop then start
sudo systemctl status pi-list.service     # check if it's running
```
