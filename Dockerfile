FROM node:20-trixie-slim AS pre-build

RUN : \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


FROM pre-build AS dev-build

WORKDIR /app

COPY . /app
RUN npm ci
RUN npm run build


FROM pre-build AS prd-build

WORKDIR /app

COPY package.json package-lock.json /app/
RUN npm ci --omit dev


FROM node:20-trixie-slim AS production

WORKDIR /app

COPY --from=dev-build /app/build /app/build
COPY --from=prd-build /app/node_modules /app/node_modules
COPY drizzle /app/drizzle
COPY package.json package-lock.json /app/
