import { migrate } from "drizzle-orm/better-sqlite3/migrator";
import { drizzle } from "drizzle-orm/better-sqlite3";
import Database from "better-sqlite3";

const { DATABASE_URL } = process.env;

const sqlite = new Database(DATABASE_URL);
try {
  const database = drizzle(sqlite);
  migrate(database, {
    migrationsFolder: "drizzle/migrations",
  });
} finally {
  sqlite.close();
}
