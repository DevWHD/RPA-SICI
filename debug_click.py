"""Debug para entender como carrega os filhos do SMS."""

from playwright.sync_api import sync_playwright
from src.config import BASE_URL, HEADLESS

with sync_playwright() as p:
    browser = p.chromium.launch(headless=HEADLESS)
    page = browser.new_page()
    
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(2000)
    
    # Encontrar SMS
    sms_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
    sms_link = None
    for link in sms_links:
        if link.text_content().strip() == "SMS":
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
            print("Expandindo SMS...")
            sms_icon.click()
            page.wait_for_timeout(1000)
        
        # CLICAR no SMS para acessar
        print("Acessando SMS...")
        sms_link.click()
        page.wait_for_timeout(1000)
        
        # Verificar HTML do nó 0
        children = sms_nodes_div.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
        if children:
            child = children[0]
            child_text = child.text_content().strip()
            child_id = child.get_attribute('id')
            child_num = child_id.replace('ContentPlaceHolder1_ua_treeviewt', '')
            
            print(f"Primeiro filho: '{child_text}' (ID: {child_id})")
            
            # Ver se está visível
            visible = page.evaluate("el => el.offsetParent !== null", child)
            print(f"Está visível na DOM: {visible}")
            
            # Ver se existe um ícone/nó
            child_icon_id = f"ContentPlaceHolder1_ua_treeviewt{child_num}i"
            child_icon = page.query_selector(f"#{child_icon_id}")
            
            print(f"Elemento: {page.evaluate('el => el.outerHTML', child)[:200]}")
            print(f"Tem ícone: {child_icon is not None}")
            
            # Clicar no nó 0 para expandir/acessar
            print(f"\nClicando em '{child_text}'...")
            child.click()
            page.wait_for_timeout(1500)
            
            # Verificar se carregou novos filhos
            all_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
            print(f"\nTotal de links na página após clicar: {len(all_links)}")
            
            # Procurar por nós que NÃO são os órgãos principais
            print("\nNós encontrados após clicar em '0':")
            count = 0
            for link in all_links:
                text = link.text_content().strip()
                link_id = link.get_attribute('id')
                
                # Filtrar apenas os que parecem ser filhos do SMS (ID > 31)
                num = int(link_id.replace('ContentPlaceHolder1_ua_treeviewt', ''))
                
                if num >= 32:  # Após SMS
                    print(f"  {text:40} | ID: {link_id}")
                    count += 1
                    if count > 25:
                        break
    
    browser.close()
