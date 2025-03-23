#!/bin/bash

# Остановить предыдущие процессы если есть
if [ -f "cloudflared.pid" ]; then
    kill $(cat cloudflared.pid) 2>/dev/null
    rm cloudflared.pid
fi

# Запустить Gunicorn
gunicorn -b 0.0.0.0:5000 wsgi:app --daemon

# Запустить Cloudflare туннель
./cloudflared tunnel --url http://localhost:5000 > cloudflared.log 2>&1 &
echo $! > cloudflared.pid

echo "Сервер запущен. Временный URL доступен в файле cloudflared.log"
echo "Для подключения постоянного домена derx.space требуется настройка в панели Cloudflare" 