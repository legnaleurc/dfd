import { drizzle } from "drizzle-orm/better-sqlite3";

import { env } from "$env/dynamic/private";

export function connect() {
  const database = drizzle(env.DATABASE_URL);
  return database;
}
