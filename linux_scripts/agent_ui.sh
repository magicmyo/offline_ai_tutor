#!/usr/bin/env bash
set -euo pipefail

#### ==== CONFIG ==== ####
MODEL_PATH="/home/offline_ai_tutor/models/qwen2.5-3b-instruct-q4_k_m.gguf"
LLAMA_PORT=8081              # llama-server API port
WEB_PORT=8082                # index.html port
AGENT_PATH="/home/offline_ai_tutor/ai_tutor_ui/"
IFACE="${IFACE:-}"           # optionally export IFACE=wlan0 or eth0
OPEN_BROWSER="${OPEN_BROWSER:-0}"  # set to 1 to xdg-open the UI
QR_OUT="${QR_OUT:-qr_ui_port_${WEB_PORT}.png}"

#### ==== helpers: IP detection & QR ==== ####
ip_of() {
  local dev="$1"
  ip -4 addr show "$dev" 2>/dev/null \
    | awk '/inet /{print $2}' | cut -d/ -f1 | grep -v '^127\.' || true
}

pick_ip() {
  local ip=""
  [[ -n "$IFACE" ]] && ip="$(ip_of "$IFACE")"
  [[ -z "$ip" ]] && ip="$(ip_of wlan0)"
  [[ -z "$ip" ]] && ip="$(ip_of eth0)"
  if [[ -z "$ip" ]]; then
    for i in $(hostname -I 2>/dev/null || true); do
      if echo "$i" | grep -q '^192\.168\.'; then
        ip="$i"; break
      fi
    done
  fi
  echo "$ip"
}

need_qrencode() {
  if ! command -v qrencode >/dev/null 2>&1; then
    echo "[..] 'qrencode' not found. Attempting to install..."
    if command -v apt >/dev/null 2>&1; then
      sudo apt update && sudo apt install -y qrencode
    else
      echo "[!!] Please install 'qrencode' manually and re-run."
      exit 1
    fi
  fi
}

#### ==== start servers ==== ####
echo "[..] Starting llama-server on port $LLAMA_PORT ..."
llama-server \
  -m "$MODEL_PATH" \
  --host 0.0.0.0 \
  --port $LLAMA_PORT \
  -c 16384 \
  -np 4 \
  >/tmp/llama-server.log 2>&1 &
LLAMA_PID=$!

echo "[..] Starting static web server on port $WEB_PORT ..."
# python3 -m http.server $WEB_PORT --bind 0.0.0.0 --directory "$(dirname "$INDEX_HTML")" 
cd "$AGENT_PATH"
python3 agent_server.py \
  >/tmp/agent-ui-web.log 2>&1 &
WEB_PID=$!

trap 'echo; echo "[..] Stopping..."; kill $LLAMA_PID $WEB_PID 2>/dev/null || true' INT TERM

# small warm-up
sleep 1

#### ==== print endpoints + QR ==== ####
IP="$(pick_ip)"
if [[ -z "$IP" ]]; then
  echo "[!!] Could not detect a LAN IP. Are you connected to a network?"
  kill $LLAMA_PID $WEB_PID 2>/dev/null || true
  exit 1
fi

UI_URL="http://${IP}:${WEB_PORT}"     # index.html is served as directory index
API_URL="http://${IP}:${LLAMA_PORT}"   # llama-server root; add /v1/chat/completions in your UI

clear

echo
echo "================= ENDPOINTS ================="
echo " Hostname       : $(hostname)"
echo " All IPs        : $(hostname -I || true)"
echo " Selected IP    : ${IP}"
echo " UI (index.html): ${UI_URL}"
echo " API (llama)    : ${API_URL}"
echo " Logs           : /tmp/llama-server.log  |  /tmp/tutor-ui-web.log"
echo "============================================="
echo

need_qrencode
echo "[..] UI QR code (scan with phone):"
qrencode -t ANSIUTF8 "$UI_URL"
#qrencode -o "$QR_OUT" -s 10 -m 2 "$UI_URL"
#echo "[OK] Saved QR image -> $QR_OUT"

if [[ "$OPEN_BROWSER" == "1" ]] && command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$UI_URL" >/dev/null 2>&1 || true
fi

# keep both services alive
wait
