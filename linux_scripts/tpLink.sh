


#!/usr/bin/env bash
set -e

sudo systemctl stop dnsmasq
#sudo systemctl stop dhcpcd

#sudo pkill dnsmasq
#sudo kill create_ap


# ===== CONFIGURATION =====
SSID="AITutor"
PASSWORD="pass12345"
WIFI_IF="wlan1"
INTERNET_IF="eth0"   # or "" for no internet sharing
SECURITY="WPA2"       # WPA, WEP, or nopass

# ===== DISCONNECT EXISTING WI-FI =====
echo "[..] Disconnecting any existing Wi-Fi connection..."
sudo nmcli dev disconnect wlan0 2>/dev/null || true
sudo ip link set wlan0 down && sudo ip link set "$WIFI_IF" up

sudo nmcli dev disconnect "$WIFI_IF" 2>/dev/null || true
sudo ip link set "$WIFI_IF" down && sudo ip link set "$WIFI_IF" up

clear

echo "=========================================="
echo "   Raspberry Pi Access Point TPLink Setup"
echo "=========================================="
echo " - Wi-Fi Name (SSID): $SSID"
echo " - Password: $PASSWORD"
echo " - Security: $SECURITY"
if [ -n "$INTERNET_IF" ]; then
    echo " - Internet Sharing: Enabled via $INTERNET_IF"
else
    echo " - Internet Sharing: Disabled (Offline LAN mode)"
fi
echo " - Current IP Address(es): $(hostname -I)"
echo "=========================================="
sleep 2

echo

sudo rfkill unblock all
sudo nmcli dev set wlan1 managed no

# ===== GENERATE QR CODE (PNG) =====
# qrencode -o wifi.png "WIFI:T:$SECURITY;S:$SSID;P:$PASSWORD;;"
# echo "[OK] QR code saved as wifi.png"

# ===== SHOW QR CODE IN TERMINAL =====
qrencode -t ANSIUTF8 "WIFI:T:$SECURITY;S:$SSID;P:$PASSWORD;;"

echo



# ===== START ACCESS POINT =====
sudo create_ap --no-virt -n "$WIFI_IF" "$SSID" "$PASSWORD" --freq-band 2.4 --country NZ --ieee80211n

#sudo create_ap --no-virt -n wlan1 AITutor pass12345--freq-band 2.4 --country NZ --ieee80211n

#sudo systemctl start dhcpcd

#sudo nano /etc/hostapd/hostapd.conf

#interface=wlan1
#driver=nl80211
#bridge=br0
#hw_mode=g
#channel=6
#ieee80211n=1
#wmm_enabled=1
#auth_algs=1
#wpa=2
#wpa_key_mgmt=WPA-PSK
#wpa_pairwise=TKIP
#rsn_pairwise=CCMP
#ssid=AI-Tutor-Pi
#wpa_passphrase=SuperSecret123

#sudo pkill hostapd
#sudo hostapd -dd /etc/hostapd/hostapd.conf 

