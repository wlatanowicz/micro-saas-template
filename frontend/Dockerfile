FROM node:20-bookworm-slim
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5173
ENTRYPOINT ["/entrypoint.sh"]
