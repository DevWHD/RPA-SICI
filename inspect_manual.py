"""Inspecionar a página manualmente."""

from playwright.sync_api import sync_playwright
from src.config import BASE_URL, HEADLESS

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Abrir visual
    page = browser.new_page()
    
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(2000)
    
    # Encontrar SMS
    sms_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
    for link in sms_links:
        text = link.text_content().strip()
        if text == "SMS":
            sms_id = link.get_attribute('id')
            sms_num = sms_id.replace('ContentPlaceHolder1_ua_treeviewt', '')
            sms_icon_id = f"ContentPlaceHolder1_ua_treeviewt{sms_num}i"
            sms_nodes_id = f"ContentPlaceHolder1_ua_treeviewn{sms_num}Nodes"
            
            # Expandir
            sms_icon = page.query_selector(f"#{sms_icon_id}")
            if sms_icon:
                print("Clicando em SMS icon para expandir...")
                sms_icon.click()
                page.wait_for_timeout(1000)
            
            # Clicar em SMS
            print("Clicando em SMS para carregar conteúdo...")
            link.click()
            page.wait_for_timeout(2000)
            
            print("\n=== HTML da árvore SMS após clicar ===")
            sms_nodes_div = page.query_selector(f"#{sms_nodes_id}")
            if sms_nodes_div:
                html = page.evaluate("el => el.outerHTML", sms_nodes_div)
                print(html[:2000])
            
            break
    
    print("\nNavigador aberto - inspecione visualmente (pressione Ctrl+C para fechar)...")
    input("Pressione ENTER para fechar o navegador...")
    browser.close()
