import { describe, expect, it } from "vitest";
import { validateAndSanitizeSql } from "../sql-guardrail";

describe("SQL AST Guardrail (`validateAndSanitizeSql`)", () => {
  it("permite query SELECT simples com portal_slug e aplica LIMIT 100", () => {
    const query =
      "SELECT * FROM fct_despesas WHERE portal_slug = 'porciuncula_prefeitura'";
    const res = validateAndSanitizeSql(query, "porciuncula_prefeitura");

    expect(res.allowed).toBe(true);
    expect(res.isAggregate).toBe(false);
    expect(res.sanitizedQuery).toContain("LIMIT 100");
  });

  it("preserva cálculos contábeis de agregação sem aplicar LIMIT 100 em SUM/GROUP BY", () => {
    const query =
      "SELECT ano, SUM(total_pago) AS total FROM fct_despesas WHERE portal_slug = 'porciuncula_prefeitura' GROUP BY ano";
    const res = validateAndSanitizeSql(query, "porciuncula_prefeitura");

    expect(res.allowed).toBe(true);
    expect(res.isAggregate).toBe(true);
    expect(res.sanitizedQuery).not.toContain("LIMIT 100");
    expect(res.sanitizedQuery).toBe(query);
  });

  it("bloqueia instruções de modificação (UPDATE, DELETE, DROP, INSERT)", () => {
    const queryUpdate =
      "UPDATE fct_despesas SET total_pago = 0 WHERE portal_slug = 'porciuncula_prefeitura'";
    const queryDrop =
      "DROP TABLE fct_despesas; SELECT * FROM fct_despesas WHERE portal_slug = 'porciuncula_prefeitura'";

    expect(validateAndSanitizeSql(queryUpdate).allowed).toBe(false);
    expect(validateAndSanitizeSql(queryDrop).allowed).toBe(false);
  });

  it("rejeita queries sem o filtro obrigatório portal_slug", () => {
    const query = "SELECT * FROM fct_despesas WHERE ano = 2025";
    const res = validateAndSanitizeSql(query);

    expect(res.allowed).toBe(false);
    expect(res.reason).toContain("portal_slug");
  });

  it("redireciona LIMITs acima de 100 para LIMIT 100 em buscas detalhadas não-agregadas", () => {
    const query =
      "SELECT * FROM fct_despesas WHERE portal_slug = 'porciuncula_prefeitura' LIMIT 500";
    const res = validateAndSanitizeSql(query);

    expect(res.allowed).toBe(true);
    expect(res.isAggregate).toBe(false);
    expect(res.sanitizedQuery).toContain("LIMIT 100");
  });
});
