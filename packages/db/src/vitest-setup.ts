import { afterAll } from "vitest";
import { closeDb } from "./client";

afterAll(async () => {
  await closeDb();
});
