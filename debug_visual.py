from playwright.sync_api import sync_playwright

BASE_URL = "https://sici.rio.rj.gov.br/PAG/principal.aspx"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    print("[*] Acessando site...")
    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')
    
    # Expandir SMS
    all_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
    for link in all_links:
        if link.text_content().strip() == "SMS":
            link.click()
            page.wait_for_timeout(300)
            break
    
    # Expandir novamente
    all_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
    for link in all_links:
        if link.text_content().strip() == "SMS":
            link.click()
            page.wait_for_timeout(300)
            break
    
    print("[*] Analisando visibilidade...")
    all_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
    
    sms_found = False
    for i, link in enumerate(all_links):
        text = link.text_content().strip()
        link_id = link.get_attribute('id')
        is_visible = link.is_visible()
        
        if text == "SMS":
            sms_found = True
            print(f"\n>>> ENCONTRADO SMS no índice {i}")
        
        if sms_found and i >= len(all_links) - 5:  # Mostrar últimos 5
            print(f"[{i}] {text:40} ID: {link_id:45} Visível: {is_visible}")
        
        if sms_found and i < 50:  # Mostrar primeiros 50 depois de SMS
            print(f"[{i}] {text:40} ID: {link_id:45} Visível: {is_visible}")
    
    print("\n[*] Aguardando para inspeção (10s)...")
    page.wait_for_timeout(10000)
    browser.close()
