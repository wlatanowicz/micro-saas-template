#!/bin/sh
set -e
if [ ! -d /app/node_modules/vite ]; then
  npm ci
fi
exec npm run dev -- --host 0.0.0.0 --port 5173
