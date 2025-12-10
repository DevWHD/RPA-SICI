"""Debug: inspecionar a estrutura DOM completa do SMS."""

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
                sms_icon.click()
                page.wait_for_timeout(1000)
            
            # Reencontrar SMS após expandir
            sms_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
            for link in sms_links:
                if link.text_content().strip() == "SMS":
                    link.click()
                    page.wait_for_timeout(1000)
                    break
            
            # Inspecionar o nó "0"
            print("=== ESTRUTURA DO NÓ '0' ===")
            children = sms_nodes_div.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
            if children:
                node_0 = children[0]
                node_0_id = node_0.get_attribute('id')
                node_0_num = node_0_id.replace('ContentPlaceHolder1_ua_treeviewt', '')
                
                # HTML do nó 0
                node_0_html = page.evaluate("el => el.outerHTML", node_0)
                print(f"HTML do nó 0:\n{node_0_html[:300]}")
                
                # Verificar ícone do nó 0
                node_0_icon_id = f"ContentPlaceHolder1_ua_treeviewt{node_0_num}i"
                node_0_nodes_id = f"ContentPlaceHolder1_ua_treeviewn{node_0_num}Nodes"
                
                node_0_icon = page.query_selector(f"#{node_0_icon_id}")
                node_0_nodes = page.query_selector(f"#{node_0_nodes_id}")
                
                print(f"\nNó 0 ({node_0_id}):")
                print(f"  Tem ícone: {node_0_icon is not None}")
                print(f"  Tem container: {node_0_nodes is not None}")
                
                if node_0_nodes:
                    display = page.evaluate("el => window.getComputedStyle(el).display", node_0_nodes)
                    print(f"  Display do container: {display}")
                    
                    # Verificar se tem filhos
                    grandchildren = node_0_nodes.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
                    print(f"  Filhos do nó 0: {len(grandchildren)}")
                    
                    if grandchildren:
                        print("\n  Primeiro 5 filhos do nó 0:")
                        for i, gc in enumerate(grandchildren[:5]):
                            gc_text = gc.text_content().strip()
                            gc_id = gc.get_attribute('id')
                            print(f"    [{i}] {gc_text:40} | {gc_id}")
            
            # Também procurar por qualquer estrutura de lista/tabela na página
            print("\n=== PROCURANDO POR TABELAS/LISTAS ===")
            tables = page.query_selector_all("table")
            lists = page.query_selector_all("ul, ol, [role='tree']")
            divs_with_class = page.query_selector_all("div[class*='Nodes']")
            
            print(f"Tabelas encontradas: {len(tables)}")
            print(f"Listas encontradas: {len(lists)}")
            print(f"Divs com 'Nodes' na classe: {len(divs_with_class)}")
            
            # Listar todos os divs que contêm "Nodes"
            print("\nDivs 'Nodes' encontrados:")
            for div in divs_with_class[:15]:
                div_id = div.get_attribute('id')
                display = page.evaluate("el => window.getComputedStyle(el).display", div)
                children_count = len(div.query_selector_all("a[id*='ua_treeview']"))
                print(f"  {div_id:50} | display: {display:10} | children: {children_count}")
            
            break
    
    browser.close()
