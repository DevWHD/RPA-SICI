"""Debug: ver o que mudou após clicar no nó 0."""

from playwright.sync_api import sync_playwright
from src.config import BASE_URL, HEADLESS

with sync_playwright() as p:
    browser = p.chromium.launch(headless=HEADLESS)
    page = browser.new_page()
    
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(2000)
    
    # Expandir SMS
    sms_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
    for link in sms_links:
        if link.text_content().strip() == "SMS":
            sms_id = link.get_attribute('id')
            sms_num = sms_id.replace('ContentPlaceHolder1_ua_treeviewt', '')
            sms_icon_id = f"ContentPlaceHolder1_ua_treeviewt{sms_num}i"
            sms_nodes_id = f"ContentPlaceHolder1_ua_treeviewn{sms_num}Nodes"
            
            sms_icon = page.query_selector(f"#{sms_icon_id}")
            if sms_icon:
                sms_icon.click()
                page.wait_for_timeout(1000)
            
            # Reencontrar SMS após expandir
            sms_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
            for link in sms_links:
                if link.text_content().strip() == "SMS":
                    link.click()
                    page.wait_for_timeout(1000)
                    break
            
            print("ANTES de clicar no nó 0:")
            sms_nodes_div = page.query_selector(f"#{sms_nodes_id}")
            if sms_nodes_div:
                children_before = sms_nodes_div.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
                print(f"  Filhos em {sms_nodes_id}: {len(children_before)}")
                for i, ch in enumerate(children_before[:5]):
                    print(f"    [{i}] {ch.text_content().strip()}")
            
            # Clicar no nó 0
            sms_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
            for link in sms_links:
                if link.text_content().strip() == "0":
                    link_id = link.get_attribute('id')
                    print(f"\nClicando no nó 0 ({link_id})...")
                    page.evaluate(f"""
                        () => {{
                            let el = document.getElementById('{link_id}');
                            if (el) el.click();
                        }}
                    """)
                    page.wait_for_load_state('networkidle')
                    page.wait_for_timeout(1500)
                    break
            
            print("\nDEPOIS de clicar no nó 0:")
            sms_nodes_div = page.query_selector(f"#{sms_nodes_id}")
            if sms_nodes_div:
                children_after = sms_nodes_div.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
                print(f"  Filhos em {sms_nodes_id}: {len(children_after)}")
                for i, ch in enumerate(children_after[:15]):
                    text = ch.text_content().strip()
                    if text:
                        print(f"    [{i}] {text[:60]}")
            
            # Procurar em toda a página
            print("\nTODOS os links na página após clicar:")
            all_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
            print(f"  Total: {len(all_links)}")
            
            # Procurar por SMS e ver onde ficam seus filhos
            sms_index = None
            for i, link in enumerate(all_links):
                if link.text_content().strip() == "SMS":
                    sms_index = i
                    print(f"\n  SMS encontrado no índice {i}")
                    # Mostrar os próximos 30 itens
                    print(f"  Próximos itens após SMS:")
                    for j in range(i+1, min(i+31, len(all_links))):
                        text = all_links[j].text_content().strip()
                        if text and text != "0":
                            print(f"    [{j-i}] {text[:60]}")
                    break
            
            break
    
    browser.close()
