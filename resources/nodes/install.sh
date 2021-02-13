
echo '################## Prepare'
mkdir -p ~/tmp && cd tmp
sudo apt-get update
sudo apt-get install -y software-properties-common
sudo apt-get install -y build-essential checkinstall zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev unzip

echo '################## Install python 3.9.1'
wget https://www.python.org/ftp/python/3.9.1/Python-3.9.1.tgz
tar zxvf Python-3.9.1.tgz
cd Python-3.9.1
./configure --enable-optimizations
make -j 12
sudo make install
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
ExecStart=/usr/bin/Xvfb :0 -screen 0 1280x720x24

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
sudo systemctl enable xvfb
sudo systemctl enable x11vnc
sudo systemctl start xvfb
sudo systemctl start x11vnc

echo '################## Install Chromium'

sudo apt-get install -y fonts-liberation libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f -y

#install chromedriver
# https://chromedriver.storage.googleapis.com/LATEST_RELEASE_88.0.4324
sudo wget https://chromedriver.storage.googleapis.com/88.0.4324.96/chromedriver_linux64.zip
sudo apt-get -y install unzip
sudo unzip chromedriver_linux64.zip
#rm chromedriver_linux64.zip
sudo chmod +x chromedriver
sudo mv -f chromedriver /usr/local/bin
cd ..

echo '################## Done !'
