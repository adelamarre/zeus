

INSTALLER=$USER
echo "Install service for user $INSTALLER"

sudo rm -f /usr/bin/venom-listener
sudo rm -f /usr/bin/venom-service
sudo cp dist/venom-service /usr/bin/venom-service
sudo chmod +x /usr/bin/venom-service

sudo systemctl disable venom-service.service
sudo rm /etc/systemd/system/venom-service.service
sudo systemctl daemon-reload

echo 'Install Venom service'


#https://sqs.eu-west-3.amazonaws.com/884650520697/18e66ed8d655f1747c9afbc572955f46
read -p 'Serner name ?' SERVERID
read -p 'Account SQS endpoint ?' ACCOUNTSQSENDPOINT
read -p 'Collector SQS endpoint ?' COLLECTORSQSENDPOINT
read -p 'Max process ?' MAXPROCESS
read -p 'Spawn insterval ?' SPAWNINTERVAL
read -p 'Stats server password ?' PASSWORD
read -p 'AWS Region ?' AWSREGION
read -p 'AWS Access Key ?' AWSACCESSKEY
read -p 'AWS Secret ?' AWSSECRET

SECRET=$(echo -n $PASSWORD | md5sum | awk '{print $1}')

mkdir -p /home/$INSTALLER/.venom
rm -f /home/$INSTALLER/.venom/config.service.ini
tee -a /home/$INSTALLER/.venom/config.service.ini > /dev/null <<EOT
[LISTENER]
server_id=${SERVERID}
account_sqs_endpoint=${ACCOUNTSQSENDPOINT}
collector_sqs_endpoint=${COLLECTORSQSENDPOINT}
max_process=${MAXPROCESS}
spawn_interval=${SPAWNINTERVAL}
secret=${SECRET}
EOT


mkdir -p /home/$INSTALLER/.aws
rm -f /home/$INSTALLER/.aws/config
tee -a /home/$INSTALLER/.aws/config > /dev/null <<EOT
[default]
region = ${AWSREGION}
aws_access_key_id=${AWSACCESSKEY}
aws_secret_access_key=${AWSSECRET}
EOT
sudo systemctl stop venom-service
sudo systemctl disable venom-service
sudo systemctl daemon-reload
sudo rm -f /etc/systemd/system/venom-service.service
sudo tee -a /etc/systemd/system/venom-service.service > /dev/null <<EOT
[Unit]
Description=Venom service
After=multi-user.target

[Service]
Type=simple
User=${INSTALLER}
Group=${INSTALLER}
WorkingDirectory=/home/${INSTALLER}
ExecStart=/usr/bin/venom --nolog --scenario spotify.service

Restart=always

[Install]
WantedBy=multi-user.target
EOT
sudo systemctl daemon-reload
sudo systemctl enable venom-service.service
sudo systemctl start venom-service

echo 'Ok, service installed'