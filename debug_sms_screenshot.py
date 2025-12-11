"""
Script para capturar screenshot da página do SMS após selecionar Informações Gerais
"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    print("[*] Acessando SICI...")
    page.goto("https://sici.rio.rj.gov.br/PAG/principal.aspx", timeout=60000)
    page.wait_for_timeout(2000)
    
    print("[*] Aguardando TreeView...")
    page.wait_for_selector("#ContentPlaceHolder1_ua_treeview", timeout=30000)
    
    # Encontrar e clicar no SMS
    print("[*] Procurando SMS...")
    nodes = page.query_selector_all("[id^='ContentPlaceHolder1_ua_treeviewt']")
    
    for node in nodes:
        text = node.text_content()
        if "SMS" in text and "Secretaria Municipal" in text:
            print(f"[OK] SMS encontrado, clicando...")
            node.click()
            page.wait_for_timeout(2000)
            break
    
    # Selecionar "Informações Gerais"
    print("[*] Selecionando 'Informações Gerais'...")
    selected = page.evaluate("""
        () => {
            let selects = document.querySelectorAll('select');
            for (let select of selects) {
                let options = select.querySelectorAll('option');
                for (let option of options) {
                    let text = option.innerText.trim();
                    if (text.includes('Informações Gerais') || text.includes('Informacoes Gerais')) {
                        select.value = option.value;
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                        return text;
                    }
                }
            }
            return null;
        }
    """)
    
    if selected:
        print(f"[OK] Selecionado '{selected}'")
        page.wait_for_timeout(3000)
    
    # Capturar screenshot
    print("[*] Capturando screenshot...")
    page.screenshot(path="screenshot_sms_info_gerais.png", full_page=True)
    print("[OK] Screenshot salvo: screenshot_sms_info_gerais.png")
    
    # Extrair TODO o texto visível
    print("\n" + "="*80)
    print("TEXTO VISÍVEL NA PÁGINA")
    print("="*80)
    
    text_content = page.evaluate("() => document.body.innerText")
    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
    
    # Procurar por linhas que contenham informações relevantes
    for idx, line in enumerate(lines):
        if any(keyword in line for keyword in ['Titular', 'Cargo', 'Endereço', 'Número', 'Daniel', 'Secretário', 'Cavalcanti']):
            print(f"\n[{idx}] {line}")
            # Mostrar contexto (5 linhas antes e depois)
            for i in range(max(0, idx-5), min(len(lines), idx+6)):
                if i != idx:
                    print(f"    [{i}] {lines[i][:100]}")
    
    print("\n[*] Pressione ENTER para fechar...")
    input()
    
    browser.close()
