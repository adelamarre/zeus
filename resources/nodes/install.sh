
echo '################## Prepare'
mkdir -p ~/tmp && cd tmp
sudo apt-get update
sudo apt-get install -y software-properties-common
sudo apt install -y build-essential checkinstall zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev unzip

echo '################## Install python 3.9.1'
wget https://www.python.org/ftp/python/3.9.1/Python-3.9.1.tgz
tar zxvf Python-3.9.1.tgz
cd Python-3.9.1
./configure --enable-optimizations --enable-shared
make -j 12
sudo make install
#sudo update-alternatives --install /usr/bin/python python /usr/local/bin/python3.9 1
#sudo update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.9 1
cd ..

echo '################## Install Xvfb & x11vnc services'
sudo apt-get -y install xvfb xserver-xorg-core xfonts-100dpi xfonts-75dpi xfonts-scalable xfonts-cyrillic
sudo apt-get -y install x11vnc
# create services
sudo tee -a /etc/systemd/system/xvfb.service > /dev/null <<EOT
[Unit]
Description=xvfb virtual screen
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/Xvfb :0 -screen 0 1280x720x24 -noreset

Restart=always

[Install]
WantedBy=multi-user.target
EOT

sudo tee -a /etc/systemd/system/x11vnc.service > /dev/null <<EOT
[Unit]
Description=x11vnc remote desktop server
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/x11vnc -display :0 -forever -shared -many -rfbauth /root/.vnc_passwd

Restart=always

[Install]
WantedBy=multi-user.target
EOT
sudo x11vnc -storepasswd ascre45th /root/.vnc_passwd
sudo systemctl daemon-reload
#sudo systemctl enable xvfb
#sudo systemctl enable x11vnc
#sudo systemctl start xvfb
#sudo systemctl start x11vnc

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
cd ..


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


echo 'Configure ssh'
cd ~/
cat <<EOT >> .ssh/config
Host *
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_rsa
EOT
cat <<EOT >> .ssh/id_rsa
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAACmFlczI1Ni1jdHIAAAAGYmNyeXB0AAAAGAAAABCuFd4k5q
TX4BCbSKdpFrIhAAAAEAAAAAEAAAAzAAAAC3NzaC1lZDI1NTE5AAAAICP15NJRCeLSldsf
ghL3phTVunLqcq6cBd1m0mUP9L9GAAAAoLN44NpNgSJB0ya1Ab+qpqf6bGHUXQgJ3+OVt/
Uh7oJK/pYgQURCW8abg7DMzfCalI0V20TdEmagPiWiwwQ+LKZEMSq1Z9zp6AQzK0yP+qAj
w3Q9q9XQQhpleTXsjMsR5R4pMhCI9ecNIRj1cmdzMjMrjehoGD8R7IHMdcg9FSV81Kaygg
Bx1hZv8vWT6JyKMH8PmBrSVr1PDLfckdqK0WI=
-----END OPENSSH PRIVATE KEY-----
EOT
cat <<EOT >> .ssh/id_rsa.pub
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICP15NJRCeLSldsfghL3phTVunLqcq6cBd1m0mUP9L9G vladimir-girard@trpan.com
EOT

chmod 600 .ssh/id_*
eval $(ssh-agent -s)

echo "Configure aws"
cd ~/
mkdir .aws
cat <<EOT >> .aws/config
[default]
region = eu-west-3
aws_access_key_id=AKIA47A3QBDFRWN4ODMK
aws_secret_access_key=++uEKu+uniIUEbu8MvbjHoTixsH98dWzm5ZhfOjp
EOT

echo "Configure git"
git config --global user.name "John Doe"
git config --global user.email johndoe@example.com

#@see https://www.digitalocean.com/community/tutorials/how-to-use-systemctl-to-manage-systemd-services-and-units
echo 'Install Zeus Listener service'
sudo tee -a /etc/systemd/system/zeus-listener.service > /dev/null <<EOT
[Unit]
Description=Zeus listener service
After=multi-user.target
User=ubuntu

[Service]
Type=simple
WorkingDirectory=/home/ubuntu/projets/zeus
ExecStart=/home/ubuntu/projets/zeus/zeus-listener-service.sh 

Restart=always

[Install]
WantedBy=multi-user.target
EOT
sudo systemctl daemon-reload

echo 'Cloning repository...' 
mkdir -p ~/projects
cd ~/projects && git clone git@github.com:adelamarre/zeus.git

echo '################## Done !'
#echo 'to download zeus: cd ~/projects && git clone git@github.com:adelamarre/zeus.git'
echo 'to activate the listener service : sudo systemctl enabled zeus-listener && sudo systemctl start zeus-listener'
echo 'Enjoy !'