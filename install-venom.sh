

INSTALLER=$USER
echo "Install venom"

sudo rm -f /usr/bin/venom
~/.local/bin/pyinstaller --onefile venom.spec
sudo cp dist/venom /usr/bin/venom
sudo chmod +x /usr/bin/venom
mkdir -p /home/$INSTALLER/.venom
touch /home/$INSTALLER/.venom/listener_proxies.txt
touch /home/$INSTALLER/.venom/register_proxies.txt
touch /home/$INSTALLER/.venom/firstname.txt
touch /home/$INSTALLER/.venom/lastname.txt
touch /home/$INSTALLER/.venom/domain.txt
touch /home/$INSTALLER/.venom/user-agents.txt

echo 'Ok, venom installed'
