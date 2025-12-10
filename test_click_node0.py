"""Clicar no nó 0 e ver o resultado."""

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
            sms_nodes_div = page.query_selector(f"#{sms_nodes_id}")
            
            if sms_icon:
                print("Expandindo SMS...")
                sms_icon.click()
                page.wait_for_timeout(1000)
            
            # Reencontrar SMS após expandir
            sms_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
            for link in sms_links:
                if link.text_content().strip() == "SMS":
                    print("Acessando SMS...")
                    link.click()
                    page.wait_for_timeout(1000)
                    break
            
            # Obter referência ao nó 0
            sms_nodes_div = page.query_selector(f"#{sms_nodes_id}")
            children = sms_nodes_div.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
            
            if children:
                node_0 = children[0]
                node_0_id = node_0.get_attribute('id')
                print(f"\nNó 0 encontrado: {node_0_id}")
                
                # Tentar clicar
                print("Clicando no nó 0...")
                try:
                    # Usar JavaScript para clicar, evitando validações
                    href = node_0.get_attribute('href')
                    print(f"Href: {href}")
                    
                    # Navegar diretamente
                    if href and href.startswith('javascript:'):
                        # Avaliar o JavaScript
                        page.evaluate("""
                            () => {
                                let el = document.querySelector('a[id="ContentPlaceHolder1_ua_treeviewt32"]');
                                if (el) {
                                    el.click();
                                }
                            }
                        """)
                        page.wait_for_load_state('networkidle')
                        page.wait_for_timeout(1500)
                    
                    print("✓ Nó 0 clicado!")
                    
                    # Verificar o URL atual
                    print(f"URL: {page.url}")
                    
                    # Procurar por novos nós
                    new_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
                    print(f"Links encontrados após clicar: {len(new_links)}")
                    
                    # Mostrar os links em torno do ID 32 (o nó 0)
                    print("\n=== Nós após expandir nó 0 ===")
                    sms_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
                    count = 0
                    in_sms_section = False
                    for link in sms_links:
                        link_id = link.get_attribute('id')
                        link_text = link.text_content().strip()
                        
                        # Pegar número do ID
                        try:
                            num = int(link_id.replace('ContentPlaceHolder1_ua_treeviewt', ''))
                        except:
                            continue
                        
                        # Se encontrar SMS, marcar seção
                        if link_text == "SMS":
                            in_sms_section = True
                            print(f">>> SMS encontrado (t{num})")
                        
                        # Mostrar nós que vêm após SMS
                        if in_sms_section and num >= 32:
                            print(f"  t{num:3d}: {link_text:40}")
                            count += 1
                            if count > 30:
                                break
                
                except Exception as e:
                    print(f"Erro: {e}")
            
            break
    
    browser.close()
