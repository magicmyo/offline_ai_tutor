sudo sed -i '/^\[keyfile\]/,/^$/d' /etc/NetworkManager/NetworkManager.conf
sudo nmcli dev set wlan0 managed yes
sudo rfkill unblock all
sudo nmcli radio wifi on
sudo systemctl restart NetworkManager
