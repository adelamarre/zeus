

INSTALLER=$USER
echo "Install service for user $INSTALLER"

sudo rm /usr/bin/venom-listener
sudo rm /usr/bin/venom-service
sudo cp dist/venom-service /usr/bin/venom-service
sudo chmod +x /usr/bin/venom-service

sudo systemctl disable venom-service.service
sudo rm /etc/systemd/system/venom-service.service
rm -rf /home/$INSTALLER/.venom
rm -rf /home/$INSTALLER/.aws

sudo systemctl daemon-reload



echo 'Install Venom service'


#https://sqs.eu-west-3.amazonaws.com/884650520697/18e66ed8d655f1747c9afbc572955f46
read -p 'SQS endpoint ?' SQSENDPOINT
read -p 'Max process ?' MAXPROCESS
read -p 'Spawn insterval ?' SPAWNINTERVAL

mkdir -p /home/$INSTALLER/.venom
tee -a /home/$INSTALLER/.venom/config.ini > /dev/null <<EOT
[LISTENER]
sqs_endpoint=${SQSENDPOINT}
max_process=${MAXPROCESS}
spawn_interval=${SPAWNINTERVAL}
EOT

read -p 'AWS Region ?' AWSREGION
read -p 'AWS Access Key ?' AWSACCESSKEY
read -p 'AWS Secret ?' AWSSECRET

mkdir -p /home/$INSTALLER/.aws
tee -a /home/$INSTALLER/.aws/config > /dev/null <<EOT
[default]
region = ${AWSREGION}
aws_access_key_id=${AWSACCESSKEY}
aws_secret_access_key=${AWSSECRET}
EOT

sudo tee -a /etc/systemd/system/venom-service.service > /dev/null <<EOT
[Unit]
Description=Venom service
After=multi-user.target

[Service]
Type=simple
User=${INSTALLER}
Group=${INSTALLER}
WorkingDirectory=/home/${INSTALLER}
ExecStart=/usr/bin/venom-service --nolog 

Restart=always

[Install]
WantedBy=multi-user.target
EOT
sudo systemctl daemon-reload
sudo systemctl enable venom-service.service
sudo systemctl start venom-service

echo 'Ok, service installed'