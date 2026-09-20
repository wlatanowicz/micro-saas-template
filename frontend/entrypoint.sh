#!/bin/sh
set -e
cd /repo
if [ ! -d /repo/node_modules ]; then
  npm ci
fi
cd /repo/frontend
exec npm run dev -- --host 0.0.0.0 --port 5173
