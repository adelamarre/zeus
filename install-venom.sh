


echo "Install venom"

sudo rm -f /usr/bin/venom
#/home/serveurspotify/.local/bin/pyinstaller --onefile venom
sudo cp dist/venom /usr/bin/venom
sudo chmod +x /usr/bin/venom

echo 'Ok, venom installed'
