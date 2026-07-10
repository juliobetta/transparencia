"""
Script de automação para baixar CSVs de Receitas do Portal da Transparência
de Porciúncula/RJ, para múltiplos anos e entidades.

Isto se deve ao fato de um bug na API do Portal das Transparencia, que não carrega dados para anos anteriores ao atual.
"""

import json
import subprocess
import time
import urllib.error
import urllib.request
from csv import writer
from datetime import date
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

BASE_URL = "https://transparencia.porciuncula.rj.gov.br/transparencia/"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHROME_EXECUTABLE = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_REMOTE_DEBUGGING_PORT = 9222

# Pasta onde os arquivos serão organizados
BASE_DOWNLOAD_DIR = PROJECT_ROOT / "data" / "csv" / "receitas"

# Perfil persistente do Chrome (mantém cookies entre execuções,
# incluindo o cookie de "clearance" do Cloudflare após resolver o desafio)
USER_DATA_DIR = PROJECT_ROOT / ".local_browsers" / "chrome_profile_transparencia"


# Anos para os quais os relatórios serão baixados. O ano atual fica sempre de
# fora: os dados dele ainda estão em andamento e mudam a cada execução.
YEARS = list(range(2017, date.today().year))

# texto exibido no dropdown -> nome da pasta
ENTITIES = [
    ("FUNDO DE SOLIDARIEDADE - FUNDESOL", "10"),
    ("FUNDO MUNICIPAL DE ASSISTENCIA SOCIAL", "3"),
    ("FUNDO MUNICIPAL DE DEFESA AMBIENTAL", "9"),
    ("FUNDO MUNICIPAL DE EDUCAÇÃO", "8"),
    ("FUNDO MUNICIPAL DE SAUDE", "2"),
    ("PREFEITURA MUNICIPAL DE PORCIÚNCULA", "7"),
]

# texto do link no submenu Receitas -> nome do arquivo
REPORTS = [
    ("Arrecadação Orçamentária - Geral", "ReceitaOrcamentaria"),
    ("Arrecadação Orçamentária - Transferências da União", "ReceitaUniao"),
    ("Arrecadação Orçamentária - Transferências do Estado", "ReceitaEstado"),
    ("Arrecadação Extra-Orçamentária", "ReceitaExtraOrcamentaria"),
]

MAX_REPORT_RETRIES = 1
FAILED_LOG_PATH = PROJECT_ROOT / "data" / "failed_requests.csv"
PROGRESS_LOG_PATH = PROJECT_ROOT / "data" / "csv" / "receitas_progress.json"


def report_key(year: int, entity_slug: str, report_slug: str) -> str:
    """Chave única de progresso por combinação ano-entidade-relatório."""
    return f"{year}|{entity_slug}|{report_slug}"


def load_progress() -> set[str]:
    """Carrega o progresso já concluído para retomar execuções interrompidas."""
    if not PROGRESS_LOG_PATH.exists():
        return set()

    try:
        data = json.loads(PROGRESS_LOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()

    completed = data.get("completed", [])
    if not isinstance(completed, list):
        return set()

    return {str(item) for item in completed}


def save_progress(completed: set[str]):
    """Persiste o progresso de forma incremental para retomada posterior."""
    PROGRESS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "completed": sorted(completed),
    }
    tmp_path = PROGRESS_LOG_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(PROGRESS_LOG_PATH)


def select_devexpress_combo(page, combo_id: str, option_text: str, timeout_ms: int = 30000):
    """Abre um ASPxComboBox da DevExpress e seleciona o item pelo texto exato."""
    input_selector = f"#{combo_id}_I"
    dropdown_selector = f"#{combo_id}_DDD_L"
    option_locator = page.locator(
        f"{dropdown_selector} td.dxeListBoxItem_DevEx:visible",
        has_text=option_text,
    ).first

    # Evita trabalho extra quando o valor já está selecionado.
    try:
        if page.locator(input_selector).input_value(timeout=1000).strip() == option_text:
            return
    except PlaywrightTimeoutError:
        pass

    # Seleção via clique real na UI: necessário para que o ASPxComboBox dispare
    # o callback de servidor (SelectedIndexChanged) que atualiza o estado da
    # sessão (ex.: exercício ativo). A API cliente (SelectItemByText/SetText +
    # RaiseValueChanged) só atualiza o texto exibido no input, sem round-trip
    # ao servidor — isso fazia os relatórios abrirem com o ano/entidade errado
    # mesmo com o combo "mostrando" o valor correto.
    last_error = None
    for _ in range(4):
        try:
            wait_for_loader_idle(page, timeout_ms=timeout_ms)

            # O botão "_B-1" alterna aberto/fechado; se o dropdown já estiver
            # aberto (estado residual de uma tentativa anterior), um novo
            # clique o fecharia em vez de abri-lo. Normaliza para "fechado"
            # antes de clicar, garantindo que o clique sempre abra a lista.
            if page.locator(dropdown_selector).is_visible():
                page.keyboard.press("Escape")
                page.locator(dropdown_selector).wait_for(state="hidden", timeout=3000)

            page.click(f"#{combo_id}_B-1", timeout=timeout_ms)
            page.locator(dropdown_selector).wait_for(state="visible", timeout=timeout_ms)
            option_locator.wait_for(state="visible", timeout=timeout_ms)
            # A lista tem uma animação de abertura; clicar durante a transição
            # às vezes não registra (handlers do item ainda não religados).
            page.wait_for_timeout(300)
            option_locator.click(timeout=timeout_ms)

            try:
                page.locator(dropdown_selector).wait_for(state="hidden", timeout=5000)
            except PlaywrightTimeoutError:
                pass

            page.wait_for_function(
                """([inputSelector, expected]) => {
                    const el = document.querySelector(inputSelector);
                    if (!el) return false;
                    const value = el.value.trim();
                    return value === expected || value.includes(expected);
                }""",
                arg=[input_selector, option_text],
                timeout=15000,
            )
            wait_for_loader_idle(page, timeout_ms=timeout_ms)
            page.wait_for_timeout(350)
            return
        except PlaywrightTimeoutError as exc:
            last_error = exc

    current_value = ""
    try:
        current_value = page.locator(input_selector).input_value(timeout=1000).strip()
    except PlaywrightTimeoutError:
        current_value = "<indisponível>"

    raise RuntimeError(
        f"Falha ao selecionar '{option_text}' no combo '{combo_id}'. Valor atual: '{current_value}'."
    ) from last_error


def try_select_devexpress_combo(page, combo_id: str, option_text: str) -> bool:
    """Seleciona item do combo; retorna False apenas quando o item não existe.

    Verifica a disponibilidade via API JS (rápido, sem interação de UI) antes
    de tentar selecionar. Isso evita esperar os timeouts/retries completos de
    select_devexpress_combo só para descobrir, por tentativa e erro, que a
    entidade não está disponível para o exercício selecionado (a lista de
    entidades é filtrada por ano).
    """
    if not combo_has_option(page, combo_id, option_text):
        return False

    try:
        select_devexpress_combo(page, combo_id, option_text, timeout_ms=4000)
        return True
    except (PlaywrightTimeoutError, RuntimeError) as exc:
        if combo_has_option(page, combo_id, option_text):
            raise RuntimeError(f"Item '{option_text}' existe no combo '{combo_id}', mas a seleção falhou.") from exc
        return False


def combo_has_option(page, combo_id: str, option_text: str) -> bool:
    """Verifica se um item existe no combo DevExpress sem depender de click visível."""
    try:
        return bool(
            page.evaluate(
                """([id, expected]) => {
                    const norm = (s) => (s || '').toString().trim().toLowerCase();
                    const target = norm(expected);
                    const getByName = globalThis.ASPxClientControl?.GetControlCollection?.().GetByName;
                    const combo = globalThis[id] || (getByName ? getByName(id) : null);
                    if (!combo || typeof combo.GetItemCount !== 'function' || typeof combo.GetItem !== 'function') {
                        return false;
                    }
                    const count = combo.GetItemCount();
                    for (let i = 0; i < count; i += 1) {
                        const item = combo.GetItem(i);
                        const text = norm(item?.text ?? item?.GetText?.() ?? '');
                        if (text === target) return true;
                    }
                    return false;
                }""",
                [combo_id, option_text],
            )
        )
    except PlaywrightError:
        return False


def open_receitas_report(page, link_text: str):
    """Abre relatório de Receitas por ação JS (mais estável que hover/click no menu)."""
    wait_for_loader_idle(page, timeout_ms=20000)

    action_id = get_report_action_id(page, link_text)
    if action_id:
        triggered = bool(
            page.evaluate(
                """(id) => {
                    if (typeof ProcessaDados !== 'function') return false;
                    ProcessaDados(id);
                    return true;
                }""",
                action_id,
            )
        )
        if not triggered:
            raise RuntimeError(f"Não foi possível disparar ProcessaDados para '{link_text}'.")
    else:
        # Fallback para o caminho visual caso o portal não exponha o onclick esperado.
        menu_item = page.locator("#LnkMenuReceitas")
        try:
            menu_item.hover(timeout=3000)
        except PlaywrightTimeoutError:
            pass
        menu_item.click(timeout=5000, force=True)
        wait_for_loader_idle(page, timeout_ms=10000)
        try:
            page.get_by_text(link_text, exact=True).click(timeout=8000)
        except PlaywrightError:
            page.get_by_text(link_text, exact=True).click(timeout=8000, force=True)

    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except PlaywrightTimeoutError:
        pass

    wait_for_loader_idle(page, timeout_ms=20000)
    page.frame_locator("#frmPaginaAspx").locator("#btnExportarCSV").wait_for(timeout=30000)
    page.wait_for_timeout(600)


def get_report_action_id(page, link_text: str) -> str | None:
    """Extrai o identificador usado por ProcessaDados a partir do texto do link."""
    try:
        action_id = page.evaluate(
            """(targetText) => {
                const normalize = (s) => (s || '').replace(/\\s+/g, ' ').trim();
                const target = normalize(targetText);
                const links = Array.from(document.querySelectorAll('a[onclick*="ProcessaDados"]'));
                const match = links.find((el) => normalize(el.textContent) === target);
                if (!match) return null;

                const onclick = match.getAttribute('onclick') || '';
                const m = onclick.match(/ProcessaDados\\('([^']+)'\\)/);
                return m ? m[1] : null;
            }""",
            link_text,
        )
    except PlaywrightError:
        return None

    if action_id is None:
        return None
    return str(action_id)


def is_transparencia_server_error(page) -> bool:
    """Detecta a página de erro do aplicativo ASP.NET do portal."""
    return page.get_by_text("Erro de Servidor no Aplicativo '/Transparencia'.").count() > 0


def restore_state_for_report(page, year: int, entity_text: str):
    """Retorna ao estado base (ano + entidade) para tentar abrir o relatório novamente."""
    last_error = None
    for _ in range(2):
        try:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=120_000)
            wait_for_transparencia_app(page)
            wait_for_loader_idle(page, timeout_ms=20000)
            select_devexpress_combo(page, "cmbExercicio", str(year))
            if not try_select_devexpress_combo(page, "cmbEntidadeContabil", entity_text):
                raise RuntimeError(f"Entidade '{entity_text}' não disponível ao restaurar estado para o ano {year}.")
            return
        except (PlaywrightTimeoutError, RuntimeError, PlaywrightError) as exc:
            last_error = exc

    raise RuntimeError(f"Falha ao restaurar estado para ano={year}, entidade='{entity_text}'.") from last_error


def process_report_with_recovery(page, link_text: str, save_path: Path) -> tuple[bool, str | None]:
    """Processa um relatório com tentativas simples (sem recuperação profunda no meio)."""
    for attempt in range(1, MAX_REPORT_RETRIES + 1):
        try:
            open_receitas_report(page, link_text)

            if is_transparencia_server_error(page):
                raise RuntimeError("Portal retornou página de erro do aplicativo.")

            download_csv(page, save_path)
            return True, None
        except (PlaywrightTimeoutError, RuntimeError, PlaywrightError) as exc:
            if page.is_closed():
                return False, "Página foi fechada durante o processamento do relatório"

            if attempt == MAX_REPORT_RETRIES:
                print(f"      -> falha após {MAX_REPORT_RETRIES} tentativas: {exc}")
                return False, str(exc)

            print(f"      -> erro na tentativa {attempt}: {exc}; tentando novamente")

    return False, "Falha desconhecida no processamento do relatório"


def append_failed_request_log(
    year: int,
    entity_slug: str,
    entity_text: str,
    report_slug: str,
    report_text: str,
    save_path: Path,
    error_text: str,
):
    """Registra falhas para retentativa posterior."""
    FAILED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_header = not FAILED_LOG_PATH.exists() or FAILED_LOG_PATH.stat().st_size == 0

    with FAILED_LOG_PATH.open("a", encoding="utf-8", newline="") as f:
        csv_writer = writer(f)
        if write_header:
            csv_writer.writerow(
                [
                    "timestamp",
                    "year",
                    "entity_slug",
                    "entity_text",
                    "report_slug",
                    "report_text",
                    "save_path",
                    "error",
                ]
            )

        csv_writer.writerow(
            [
                time.strftime("%Y-%m-%d %H:%M:%S"),
                year,
                entity_slug,
                entity_text,
                report_slug,
                report_text,
                str(save_path),
                error_text,
            ]
        )


def normalize_csv_to_utf8(file_path: Path):
    """Converte o CSV para UTF-8, preservando o conteúdo textual."""
    raw = file_path.read_bytes()
    last_error = None

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError as exc:
            last_error = exc
    else:
        raise UnicodeDecodeError(
            "utf-8",
            raw,
            0,
            1,
            f"Falha ao decodificar CSV em encodings conhecidos: {last_error}",
        )

    with file_path.open("w", encoding="utf-8", newline="") as f:
        f.write(text)


def download_csv(page, save_path: Path):
    """Clica no botão CSV dentro do iframe do relatório e salva o download."""
    frame = page.frame_locator("#frmPaginaAspx")
    wait_for_loader_idle(page, timeout_ms=20000)
    with page.expect_download() as download_info:
        frame.locator("#btnExportarCSV").click(timeout=8000, force=True)
    download = download_info.value
    save_path.parent.mkdir(parents=True, exist_ok=True)
    download.save_as(save_path)
    normalize_csv_to_utf8(save_path)
    print(f"  -> salvo em {save_path} (UTF-8)")


def wait_for_transparencia_app(page, timeout_ms: int = 120_000):
    """Espera a interface autenticada carregar após a verificação manual."""
    page.wait_for_load_state("domcontentloaded")
    page.locator("#LnkMenuReceitas").wait_for(state="visible", timeout=timeout_ms)
    neutralize_modal_loader(page)
    # Pequena folga para os scripts DevExpress terminarem de registrar seus
    # handlers de clique/callback antes de qualquer interação com os combos;
    # sem essa espera, a seleção de ano/entidade fica instável logo após o
    # carregamento (o clique acontece antes do controle estar pronto).
    page.wait_for_timeout(800)


def neutralize_modal_loader(page):
    """Garante que o overlay de loading nunca bloqueie cliques/inputs.

    context.add_init_script não é confiável aqui: a página é conectada via
    CDP a uma aba do Chrome já aberta fora do controle do Playwright, então
    scripts de inicialização registrados no contexto não são anexados de
    forma consistente a esse alvo. Em vez disso, injeta o CSS diretamente
    após cada carregamento de página (o portal recarrega via page.goto a
    cada troca de ano/entidade em restore_state_for_report).
    """
    try:
        page.evaluate(
            """() => {
                if (document.getElementById('_noModalLoaderBlock')) return;
                const style = document.createElement('style');
                style.id = '_noModalLoaderBlock';
                style.textContent = '#_divModalLoader { pointer-events: none !important; }';
                document.head.appendChild(style);
            }"""
        )
    except PlaywrightError:
        pass


def wait_for_loader_idle(page, timeout_ms: int = 20000) -> bool:
    """Aguarda o overlay de loading não bloquear interações.

    Retorna True quando o loader libera a UI, False quando permanece travado.
    """
    try:
        page.wait_for_function(
            """() => {
                const el = document.querySelector('#_divModalLoader');
                if (!el) return true;
                const style = window.getComputedStyle(el);
                const isHidden =
                    style.display === 'none' ||
                    style.visibility === 'hidden' ||
                    Number(style.opacity) === 0 ||
                    el.clientHeight === 0 ||
                    el.clientWidth === 0;
                return isHidden;
            }""",
            timeout=timeout_ms,
        )
        return True
    except PlaywrightTimeoutError:
        # Fallback: alguns erros JS no portal deixam o loader preso,
        # mas os controles já estão prontos para uso.
        try:
            page_is_interactive = bool(
                page.evaluate(
                    """() => {
                        const yearInput = document.querySelector('#cmbExercicio_I');
                        const entityInput = document.querySelector('#cmbEntidadeContabil_I');
                        const exportBtn = document.querySelector('#frmPaginaAspx');

                        const yearReady = !!yearInput && !yearInput.disabled;
                        const entityReady = !!entityInput && !entityInput.disabled;
                        const reportReady = !!exportBtn;

                        return (yearReady && entityReady) || reportReady;
                    }"""
                )
            )
        except PlaywrightError:
            page_is_interactive = False

        if page_is_interactive:
            try:
                page.evaluate(
                    """() => {
                        const el = document.querySelector('#_divModalLoader');
                        if (!el) return;
                        el.style.display = 'none';
                        el.style.visibility = 'hidden';
                        el.style.opacity = '0';
                        el.style.pointerEvents = 'none';
                    }"""
                )
                return True
            except PlaywrightError:
                return False

        return False


def launch_chrome_with_remote_debugging():
    """Inicia o Chrome como app normal e expõe CDP em uma porta local."""
    subprocess.Popen(
        [
            CHROME_EXECUTABLE,
            f"--remote-debugging-port={CHROME_REMOTE_DEBUGGING_PORT}",
            f"--user-data-dir={USER_DATA_DIR}",
            "--no-first-run",
            "--new-window",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def wait_for_cdp_endpoint(timeout_ms: int = 30_000):
    """Aguarda o endpoint CDP do Chrome ficar disponível."""
    endpoint = f"http://127.0.0.1:{CHROME_REMOTE_DEBUGGING_PORT}/json/version"
    deadline = time.time() + timeout_ms / 1000
    last_error = None

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(endpoint, timeout=2) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            time.sleep(0.5)

    raise RuntimeError(
        f"Chrome não expôs CDP na porta {CHROME_REMOTE_DEBUGGING_PORT} dentro do tempo limite."
    ) from last_error


def main():
    if not Path(CHROME_EXECUTABLE).exists():
        raise FileNotFoundError(f"Chrome não encontrado em {CHROME_EXECUTABLE}.")

    launch_chrome_with_remote_debugging()
    wait_for_cdp_endpoint()
    completed_reports = load_progress()
    if completed_reports:
        print(f"Retomando progresso: {len(completed_reports)} relatório(s) já concluído(s).")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{CHROME_REMOTE_DEBUGGING_PORT}")
        if not browser.contexts:
            raise RuntimeError("Chrome conectou, mas nenhum contexto foi encontrado via CDP.")

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        page.bring_to_front()
        print(f"Abrindo {BASE_URL}...")
        response = page.goto(BASE_URL, wait_until="domcontentloaded", timeout=120_000)
        print(f"Página atual: {page.url}")
        if response is not None:
            print(f"HTTP: {response.status}")

        print("Se aparecer o desafio do Cloudflare, resolva-o manualmente na janela do navegador.")
        print("Aguardando a interface autenticada carregar...")
        try:
            wait_for_transparencia_app(page)
        except PlaywrightTimeoutError as exc:
            raise RuntimeError(
                "A interface autenticada não carregou após a verificação manual. "
                "Confira se o desafio foi concluído na janela do Chrome e tente novamente."
            ) from exc

        for year in YEARS:
            print(f"\n=== Ano {year} ===")
            for entity_text, entity_slug in ENTITIES:
                # Pula a combinação inteira sem tocar no navegador quando todos
                # os relatórios já foram baixados: evita o custo de restaurar
                # estado (reload + seleção de ano/entidade) só para descobrir,
                # relatório por relatório, que não há nada a fazer.
                pending_reports = [
                    (link_text, report_slug)
                    for link_text, report_slug in REPORTS
                    if report_key(year, entity_slug, report_slug) not in completed_reports
                ]
                if not pending_reports:
                    print(f"  -- Entidade: {entity_text} -> já concluída; pulando")
                    continue

                print(f"  -- Entidade: {entity_text}")
                try:
                    restore_state_for_report(page, year, entity_text)
                except RuntimeError as exc:
                    print(f"     -> não foi possível preparar estado para essa entidade: {exc}")
                    continue

                for link_text, report_slug in pending_reports:
                    print(f"    Relatório: {link_text}")
                    save_path = BASE_DOWNLOAD_DIR / f"{entity_slug}_{year}_{report_slug}.csv"
                    current_key = report_key(year, entity_slug, report_slug)

                    # Reposiciona estado antes de cada relatório para evitar herança de estado quebrado.
                    try:
                        restore_state_for_report(page, year, entity_text)
                    except RuntimeError as prep_exc:
                        print(f"      -> falha ao preparar estado antes do relatório: {prep_exc}")
                        append_failed_request_log(
                            year,
                            entity_slug,
                            entity_text,
                            report_slug,
                            link_text,
                            save_path,
                            str(prep_exc),
                        )
                        continue

                    ok, error_text = process_report_with_recovery(
                        page,
                        link_text,
                        save_path,
                    )
                    if not ok:
                        print("      -> pulando relatório e seguindo")
                        append_failed_request_log(
                            year,
                            entity_slug,
                            entity_text,
                            report_slug,
                            link_text,
                            save_path,
                            error_text or "Falha sem detalhe",
                        )
                        continue

                    completed_reports.add(current_key)
                    save_progress(completed_reports)

        print("\nConcluído! Todos os arquivos foram baixados.")
        browser.close()


if __name__ == "__main__":
    main()
