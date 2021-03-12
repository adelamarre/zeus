

INSTALLER=$USER
echo "Install Venom Collector service for user $INSTALLER"

sudo systemctl disable venom-collector.service
sudo rm -f /etc/systemd/system/venom-collector.service
sudo systemctl daemon-reload

echo 'Install Venom service'
sudo systemctl stop venom-collector
sudo systemctl disable venom-collector
sudo systemctl daemon-reload
sudo rm -f /etc/systemd/system/venom-collector.service
sudo tee -a /etc/systemd/system/venom-collector.service > /dev/null <<EOT
[Unit]
Description=Venom service
After=multi-user.target

[Service]
Type=simple
User=${INSTALLER}
Group=${INSTALLER}
WorkingDirectory=/home/${INSTALLER}
ExecStart=/usr/bin/venom --scenario system.collector

Restart=always

[Install]
WantedBy=multi-user.target
EOT
sudo systemctl daemon-reload
sudo systemctl enable venom-service.service
sudo systemctl start venom-service

echo 'Ok, service installed'