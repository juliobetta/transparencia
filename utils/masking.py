import re


def is_cpf(documento: str) -> bool:
    """Verifica se uma string parece um CPF (11 dígitos ou formato mascarado)."""
    # Remove caracteres de formatação
    clean = re.sub(r"\D", "", documento)
    return len(clean) == 11


def mask_cpf(cpf: str) -> str:
    """
    Mascara CPF. Se já estiver mascarado, mantém o padrão.
    Se não, aplica: 114.XXX.XXX-13
    """
    clean = re.sub(r"\D", "", cpf)

    # Se já parece mascarado ou é muito curto/longo, retorna como está ou aplica regra genérica
    if len(clean) != 11:
        return cpf  # Ou logar aviso

    return f"{clean[0:3]}.XXX.XXX-{clean[9:11]}"


def mask_name(nome: str) -> str:
    """Aplica mascaramento básico em nomes de pessoas físicas, retornando apenas as iniciais."""
    # Ex: 'JOAO GILBERTO SILVA' -> 'JGS'
    parts = nome.split()
    initials = "".join([p[0] for p in parts if p])
    return initials
