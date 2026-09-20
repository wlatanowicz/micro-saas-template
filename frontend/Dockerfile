FROM node:22-bookworm-slim
WORKDIR /repo

COPY package.json package-lock.json ./
COPY packages ./packages
COPY frontend/package.json ./frontend/package.json
COPY mobile/package.json ./mobile/package.json
RUN npm ci

COPY frontend ./frontend
COPY frontend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /repo/frontend
EXPOSE 5173
ENTRYPOINT ["/entrypoint.sh"]
