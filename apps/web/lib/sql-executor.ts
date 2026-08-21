import { executeRawSql } from "@transparencia/db";

export async function executeAnalyticsQuery<T = Record<string, unknown>>(
  sqlQuery: string,
): Promise<T[]> {
  const rawRows = await executeRawSql<Record<string, unknown>>(sqlQuery);

  // Converter BigInt de volta para Number seguro se aplicável
  const sanitizedRows = rawRows.map((row) => {
    const cleanObj: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(row)) {
      if (val == null) {
        cleanObj[key] = val;
      } else if (typeof val === "bigint") {
        cleanObj[key] = Number(val);
      } else {
        cleanObj[key] = val;
      }
    }
    return cleanObj as T;
  });

  return sanitizedRows;
}
