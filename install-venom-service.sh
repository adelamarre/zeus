

INSTALLER=$USER
echo "Install service for user $INSTALLER"

sudo rm /usr/bin/venom-listener
sudo cp dist/venom-listener /usr/bin/venom-listener
sudo chmod +x /usr/bin/venom-listener

sudo systemctl disable venom-listener.service
sudo rm /etc/systemd/system/venom-listener.service
rm -rf /home/$INSTALLER/.venom
rm -rf /home/$INSTALLER/.aws

sudo systemctl daemon-reload



echo 'Install Venom Listener service'


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
override_playlist=https://open.spotify.com/playlist/2zRgdFbmBuftCrGt47ImfE
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

sudo tee -a /etc/systemd/system/venom-listener.service > /dev/null <<EOT
[Unit]
Description=Venom listener service
After=multi-user.target


[Service]
Type=simple
User=${INSTALLER}
Group=${INSTALLER}
WorkingDirectory=/home/${INSTALLER}
ExecStart=/usr/bin/venom-listener --nolog 

Restart=always

[Install]
WantedBy=multi-user.target
EOT
sudo systemctl daemon-reload
sudo systemctl enable venom-listener.service
sudo systemctl start venom-listener


echo 'Ok, service installed'