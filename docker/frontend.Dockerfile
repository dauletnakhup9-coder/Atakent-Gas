FROM node:24-bookworm-slim AS build
WORKDIR /srv
ENV NEXT_TELEMETRY_DISABLED=1 INTERNAL_API_URL=http://backend:8000
COPY apps/admin-web/package.json apps/admin-web/package-lock.json ./
RUN npm ci
COPY apps/admin-web ./
RUN npm run build

FROM node:24-bookworm-slim AS run
WORKDIR /srv
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
COPY --from=build --chown=node:node /srv/.next/standalone ./
COPY --from=build --chown=node:node /srv/.next/static ./.next/static
USER node
EXPOSE 3000
CMD ["node", "server.js"]
