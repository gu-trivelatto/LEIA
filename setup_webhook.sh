BOT_TOKEN="8396614197:AAFJddMpbDub0ZMUQmMil-j_2CE7yBwW97I"
WEBHOOK_URL="https://oisumida.rs/leia/telegram/webhook"

curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
     -H "Content-Type: application/json" \
     -d "{\"url\": \"${WEBHOOK_URL}\", \"max_connections\": 1, \"drop_pending_updates\": true}"

echo -e "\nWebhook setup request sent!"

echo "Checking webhook info..."
curl -X GET "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
