FROM node:20.11-alpine AS build
WORKDIR /app
COPY . .
RUN npm ci && npm run build

FROM node:20.11-alpine
COPY --from=build /app/dist /app
CMD ["node", "/app/server.js"]
