"""Debug script para entender a estrutura da árvore."""

from playwright.sync_api import sync_playwright
from src.config import BASE_URL, HEADLESS

with sync_playwright() as p:
    browser = p.chromium.launch(headless=HEADLESS)
    page = browser.new_page()
    
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(2000)
    
    # Encontrar SMS
    sms_link = None
    sms_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
    
    for link in sms_links:
        text = link.text_content().strip()
        if text == "SMS":
            sms_link = link
            break
    
    if sms_link:
        sms_id = sms_link.get_attribute('id')
        sms_num = sms_id.replace('ContentPlaceHolder1_ua_treeviewt', '')
        sms_icon_id = f"ContentPlaceHolder1_ua_treeviewt{sms_num}i"
        sms_nodes_id = f"ContentPlaceHolder1_ua_treeviewn{sms_num}Nodes"
        
        sms_icon = page.query_selector(f"#{sms_icon_id}")
        sms_nodes_div = page.query_selector(f"#{sms_nodes_id}")
        
        # Expandir SMS
        if sms_icon and sms_nodes_div:
            display = page.evaluate("el => window.getComputedStyle(el).display", sms_nodes_div)
            if display == "none":
                print("Expandindo SMS...")
                sms_icon.click()
                page.wait_for_timeout(1000)
        
        # Agora obter e expandir o nó "0" (o primeiro filho)
        children_of_sms = sms_nodes_div.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
        print(f"Filhos diretos de SMS: {len(children_of_sms)}")
        
        if children_of_sms:
            first_child = children_of_sms[0]
            first_child_text = first_child.text_content().strip()
            first_child_id = first_child.get_attribute('id')
            first_child_num = first_child_id.replace('ContentPlaceHolder1_ua_treeviewt', '')
            
            print(f"Primeiro filho: '{first_child_text}' (ID: {first_child_id})")
            
            # Verificar se tem ícone/filhos
            child_icon_id = f"ContentPlaceHolder1_ua_treeviewt{first_child_num}i"
            child_icon = page.query_selector(f"#{child_icon_id}")
            child_nodes_id = f"ContentPlaceHolder1_ua_treeviewn{first_child_num}Nodes"
            child_nodes_div = page.query_selector(f"#{child_nodes_id}")
            
            print(f"Tem ícone: {child_icon is not None}")
            print(f"Tem container de filhos: {child_nodes_div is not None}")
            
            if child_icon and child_nodes_div:
                display = page.evaluate("el => window.getComputedStyle(el).display", child_nodes_div)
                print(f"Display do container de filhos: {display}")
                
                if display == "none":
                    print(f"Expandindo '{first_child_text}'...")
                    child_icon.click()
                    page.wait_for_timeout(1000)
                    
                    display = page.evaluate("el => window.getComputedStyle(el).display", child_nodes_div)
                    print(f"Display após expansão: {display}")
                
                # Obter filhos do primeiro filho
                grandchildren = child_nodes_div.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
                print(f"\nNetos encontrados: {len(grandchildren)}")
                
                for i, grandchild in enumerate(grandchildren[:20]):  # Primeiros 20
                    gc_text = grandchild.text_content().strip()
                    gc_id = grandchild.get_attribute('id')
                    print(f"  [{i:2d}] {gc_text:40} | ID: {gc_id}")
    
    browser.close()
