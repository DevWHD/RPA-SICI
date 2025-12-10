from playwright.sync_api import sync_playwright
import json

BASE_URL = "https://sici.rio.rj.gov.br/PAG/principal.aspx"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    print("[*] Acessando site...")
    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')
    
    print("[*] Expandindo SMS...")
    
    # Primeira expansão
    all_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
    for link in all_links:
        if link.text_content().strip() == "SMS":
            link.click()
            break
    page.wait_for_timeout(500)
    
    print("[*] Expandindo SMS novamente para ver filhos...")
    # Refazer a query porque referência pode ficar stale
    all_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
    for link in all_links:
        if link.text_content().strip() == "SMS":
            link.click()
            break
    page.wait_for_timeout(500)
    
    print("[*] Clicando no nó '0'...")
    all_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
    print(f"Total de links ANTES: {len(all_links)}")
    
    # Procurar nó "0" (t2) - REFAZER QUERY A CADA TENTATIVA
    found_zero = False
    for attempt in range(3):
        all_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
        for link in all_links:
            text = link.text_content().strip()
            link_id = link.get_attribute('id')
            if text == "0":
                print(f"  Tentativa {attempt+1}: Encontrado nó '0' com ID: {link_id}")
                try:
                    link.click()
                    page.wait_for_load_state('networkidle')
                    found_zero = True
                    break
                except Exception as e:
                    print(f"    Erro ao clicar: {e}")
                    page.wait_for_timeout(300)
                    continue
        if found_zero:
            break
    
    # Re-contar links
    all_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
    print(f"Total de links DEPOIS: {len(all_links)}")
    
    print("\n[*] Procurando SMS e seus filhos...")
    sms_index = None
    filhos_sms = []
    
    for i, link in enumerate(all_links):
        text = link.text_content().strip()
        link_id = link.get_attribute('id')
        if i < 50:  # Debugar primeiros 50
            print(f"  [{i}] {text:40} ID: {link_id}")
        
        if text == "SMS":
            sms_index = i
            print(f"\n✓ SMS encontrado no índice {i}")
    
    if sms_index is not None:
        print(f"\n[*] Filhos do SMS (começando do índice {sms_index + 1}):")
        for i in range(sms_index + 1, min(sms_index + 25, len(all_links))):
            link = all_links[i]
            text = link.text_content().strip()
            link_id = link.get_attribute('id')
            print(f"  [{i - sms_index - 1}] {text:40} ID: {link_id}")
            
            # Parar se encontrar próximo órgão
            if len(text) <= 4 and text.isupper() and text != "SMS":
                print(f"  ↓ Próximo órgão encontrado: {text}, parando")
                break
    
    browser.close()
