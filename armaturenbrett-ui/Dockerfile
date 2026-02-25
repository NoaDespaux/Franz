FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# We use NEXT_PUBLIC variables to configure API endpoint if needed
# For local dev, we might just proxy or point directly.

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
