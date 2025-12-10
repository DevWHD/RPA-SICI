from playwright.sync_api import sync_playwright
import json

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
    
    print("[*] Antes de clicar no nó '0' do SMS:")
    all_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
    
    # Verificar quantos filhos SMS tem
    sms_index = None
    zero_after_sms = None
    
    for i, link in enumerate(all_links):
        text = link.text_content().strip()
        if text == "SMS":
            sms_index = i
            # Próximo deve ser "0"
            if i + 1 < len(all_links):
                next_link = all_links[i + 1]
                next_text = next_link.text_content().strip()
                next_id = next_link.get_attribute('id')
                if next_text == "0":
                    zero_after_sms = next_link
                    print(f"  SMS está em índice {i}")
                    print(f"  Nó '0' de SMS está em índice {i+1} com ID: {next_id}")
            break
    
    # CONTAR filhos visíveis ANTES
    if sms_index is not None:
        children_before = 0
        for i in range(sms_index + 1, len(all_links)):
            link = all_links[i]
            text = link.text_content().strip()
            if text == "SMS":
                break
            # Aqui temos próximos órgãos, parar
            if len(text) <= 4 and text.isupper():
                print(f"  Próximo órgão: {text}")
                break
            if text and text != "0":
                children_before += 1
                if children_before <= 5:
                    print(f"    [{children_before}] {text}")
        print(f"  Total de filhos visíveis antes: {children_before}")
    
    # CLICAR no nó "0" do SMS
    if zero_after_sms:
        print("\n[*] Clicando no nó '0' do SMS...")
        try:
            # Tentar usar evaluate para clicar (pode funcionar melhor)
            page.evaluate(f"""
                document.getElementById('ContentPlaceHolder1_ua_treeviewt32').click();
            """)
            page.wait_for_load_state('networkidle')
            print("  ✓ Clique executado via JavaScript")
        except Exception as e:
            print(f"  ✗ Erro: {e}")
    
    print("\n[*] Depois de clicar no nó '0' do SMS:")
    all_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
    
    # CONTAR filhos visíveis DEPOIS
    if sms_index is not None:
        children_after = 0
        child_texts = []
        for i in range(sms_index + 1, len(all_links)):
            link = all_links[i]
            text = link.text_content().strip()
            if text == "SMS":
                break
            # Próximos órgãos
            if len(text) <= 4 and text.isupper() and text != "SMS":
                print(f"  Próximo órgão: {text}")
                break
            if text and text != "0":
                children_after += 1
                child_texts.append(text)
                if children_after <= 10:
                    print(f"    [{children_after}] {text}")
        print(f"  Total de filhos visíveis depois: {children_after}")
        
        if children_after > 5:
            print("\n  ✓✓✓ FUNCIONOU! Filhos foram revelados!")
        
        # Salvar lista de filhos
        output = {
            "antes": children_before,
            "depois": children_after,
            "filhos": child_texts
        }
        with open("debug_filhos.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n[*] Aguardando para inspeção (5s)...")
    page.wait_for_timeout(5000)
    browser.close()
