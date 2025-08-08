FROM node:20-bookworm-slim AS pre-build

RUN : \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER node


FROM pre-build AS server-build

WORKDIR /app

COPY . /app
RUN npm ci
RUN npm run build


FROM pre-build AS migration-build

WORKDIR /app

COPY package.json package-lock.json /app/
RUN npm ci --omit dev


FROM node:20-bookworm-slim AS server

USER node
WORKDIR /app

COPY --chown=node:node --from=server-build /app/build /app/build


FROM node:20-bookworm-slim AS migration

USER node
WORKDIR /app

COPY --chown=node:node --from=migration-build /app/node_modules /app/node_modules
COPY --chown=node:node drizzle /app/drizzle
COPY --chown=node:node package.json package-lock.json /app/
