#!/bin/bash

mkdir -p ~/tmp
cd ~/tmp

echo '################## Prepare'
sudo apt-get update
sudo apt-get install -y software-properties-common
sudo apt install -y build-essential checkinstall zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev unzip
sudo apt install -y python3-dev

echo '################## Install Xvfb & x11vnc services'
sudo apt-get -y install xvfb xserver-xorg-core xfonts-100dpi xfonts-75dpi xfonts-scalable xfonts-cyrillic
sudo apt-get -y install x11vnc

echo '################## Install Chromium'
sudo apt-get install -y fonts-liberation libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0
#wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
wget http://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_85.0.4183.83-1_amd64.deb
sudo dpkg -i google-chrome-stable_85.0.4183.83-1_amd64.deb
sudo apt-get install -f -y

#install chromedriver
# https://chromedriver.storage.googleapis.com/LATEST_RELEASE_88.0.4324
# https://chromedriver.storage.googleapis.com/LATEST_RELEASE_85.0.4183
# http://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_78.0.3904.87-1_amd64.deb
# http://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_85.0.4183.83-1_amd64.deb
#sudo wget https://chromedriver.storage.googleapis.com/88.0.4324.96/chromedriver_linux64.zip
sudo wget https://chromedriver.storage.googleapis.com/85.0.4183.87/chromedriver_linux64.zip
sudo apt-get -y install unzip
sudo unzip chromedriver_linux64.zip
#rm chromedriver_linux64.zip
sudo chmod +x chromedriver
sudo mv -f chromedriver /usr/local/bin



sudo tee -a /etc/systemd/system.conf > /dev/null <<EOT
DefaultTasksMax=infinity
DefaultLimitNOFILE=10000000
EOT

sudo tee -a /etc/systemd/logind.conf > /dev/null <<EOT
UserTasksMax=infinity
EOT

sudo tee -a /etc/security/limits.conf > /dev/null <<EOT
* soft     nproc          unlimited
* hard     nproc          unlimited
* soft     nofile         unlimited
* hard     nofile         unlimited
root soft     nofile         unlimited
root hard     nofile         unlimited
EOT

cd -

echo 'Done !'