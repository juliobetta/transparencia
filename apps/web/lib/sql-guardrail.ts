export interface SqlGuardrailResult {
  allowed: boolean;
  sanitizedQuery: string;
  isAggregate: boolean;
  reason?: string;
}

const FORBIDDEN_KEYWORDS = [
  "INSERT",
  "UPDATE",
  "DELETE",
  "DROP",
  "ALTER",
  "TRUNCATE",
  "CREATE",
  "GRANT",
  "REVOKE",
  "EXEC",
  "EXECUTE",
];

const AGGREGATE_PATTERNS = [
  /\bSUM\s*\(/i,
  /\bAVG\s*\(/i,
  /\bCOUNT\s*\(/i,
  /\bMAX\s*\(/i,
  /\bMIN\s*\(/i,
  /\bGROUP\s+BY\b/i,
];

function stripSqlComments(sql: string): string {
  // Remove comentários multilinha /* ... */ e linha única -- ...
  return sql
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/--.*$/gm, "")
    .trim();
}

export function validateAndSanitizeSql(
  sqlQuery: string,
  requiredPortalSlug?: string,
): SqlGuardrailResult {
  const cleanSql = stripSqlComments(sqlQuery);

  // 1. Validar presença de instrução SQL
  if (!cleanSql) {
    return {
      allowed: false,
      sanitizedQuery: "",
      isAggregate: false,
      reason: "Query SQL vazia.",
    };
  }

  // 2. Bloquear palavras-chave de modificação ou DDL
  const upperSql = cleanSql.toUpperCase();
  for (const keyword of FORBIDDEN_KEYWORDS) {
    const regex = new RegExp(`\\b${keyword}\\b`, "i");
    if (regex.test(upperSql)) {
      return {
        allowed: false,
        sanitizedQuery: cleanSql,
        isAggregate: false,
        reason: `Comando não permitido detectado: ${keyword}. Apenas consultas SELECT são autorizadas.`,
      };
    }
  }

  // 3. Garantir que a instrução inicia com SELECT ou WITH ... SELECT
  if (!upperSql.startsWith("SELECT") && !upperSql.startsWith("WITH")) {
    return {
      allowed: false,
      sanitizedQuery: cleanSql,
      isAggregate: false,
      reason: "A query deve iniciar obrigatoriamente com SELECT ou WITH.",
    };
  }

  // 4. Validar obrigatoriedade da cláusula/filtro portal_slug na instrução limpa
  const hasPortalSlugFilter = /portal_slug/i.test(cleanSql);
  if (!hasPortalSlugFilter) {
    return {
      allowed: false,
      sanitizedQuery: cleanSql,
      isAggregate: false,
      reason:
        "A query SQL deve conter obrigatoriamente o filtro portal_slug para isolamento multi-tenant.",
    };
  }

  if (
    requiredPortalSlug &&
    !cleanSql.toLowerCase().includes(requiredPortalSlug.toLowerCase())
  ) {
    return {
      allowed: false,
      sanitizedQuery: cleanSql,
      isAggregate: false,
      reason: `A query deve filtrar especificamente o tenant '${requiredPortalSlug}'.`,
    };
  }

  // 5. Verificar se é uma query de agregação contábil
  const isAggregate = AGGREGATE_PATTERNS.some((pattern) =>
    pattern.test(cleanSql),
  );

  let sanitizedQuery = cleanSql;

  // 6. Aplicar LIMIT 100 exclusivamente em buscas detalhadas / não-agregadas
  if (!isAggregate) {
    const hasLimit = /\bLIMIT\s+(\d+)/i.exec(cleanSql);
    if (!hasLimit) {
      // Adicionar LIMIT 100 se não houver cláusula LIMIT
      sanitizedQuery = `${cleanSql.replace(/;?\s*$/, "")} LIMIT 100`;
    } else {
      const currentLimit = Number.parseInt(hasLimit[1], 10);
      if (currentLimit > 100) {
        // Reduzir limite se exceder 100 registros em buscas detalhadas
        sanitizedQuery = cleanSql.replace(/\bLIMIT\s+\d+/i, "LIMIT 100");
      }
    }
  }

  return {
    allowed: true,
    sanitizedQuery,
    isAggregate,
  };
}
