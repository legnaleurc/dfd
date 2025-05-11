import { drizzle } from "drizzle-orm/better-sqlite3";

import { DATABASE_URL } from "$env/static/private";

export function connect() {
  const database = drizzle(DATABASE_URL);
  return database;
}
