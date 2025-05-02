import { drizzle } from "drizzle-orm/better-sqlite3";

import { SQLITE_FILE } from "$env/static/private";

export function connect() {
  const database = drizzle(SQLITE_FILE);
  return database;
}
