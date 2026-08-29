FROM oven/bun:1-alpine AS build
WORKDIR /usr/src/app
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun run build

FROM oven/bun:1-alpine
ENV NODE_ENV=production
WORKDIR /usr/src/app
COPY --from=build /usr/src/app/.output ./.output
EXPOSE 3000
CMD ["bun", ".output/server/index.mjs"]
