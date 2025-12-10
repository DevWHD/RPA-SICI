"""
Script para testar se os cliques estão funcionando no TreeView SICI.
"""
from playwright.sync_api import sync_playwright

p = sync_playwright().start()
try:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    page.goto('https://sici.rio.rj.gov.br/PAG/principal.aspx', wait_until='networkidle')
    page.wait_for_timeout(2000)
    
    # Encontrar primeiro ícone com filhos ocultos
    icons = page.query_selector_all("a[id*='ua_treeview'][id$='i']")
    print(f"Total de ícones: {len(icons)}")
    
    # Encontrar o primeiro que tem filhos ocultos
    for icon in icons:
        icon_id = icon.get_attribute('id')
        node_num = icon_id.replace('ContentPlaceHolder1_ua_treeview', '').replace('i', '')
        node_num = node_num.replace('t', '')
        nodes_id = f"ContentPlaceHolder1_ua_treeviewn{node_num}Nodes"
        nodes_div = page.query_selector(f"#{nodes_id}")
        
        if nodes_div:
            display = page.evaluate("el => window.getComputedStyle(el).display", nodes_div)
            if display == "none":
                print(f"\n✅ Primeiro colapsado encontrado: {icon_id}")
                print(f"   Container: {nodes_id}")
                print(f"   Display antes: {display}")
                
                # Tentar clicar
                icon.scroll_into_view_if_needed()
                print(f"   Clicando...")
                icon.click()
                page.wait_for_timeout(500)
                
                # Verificar depois
                display_after = page.evaluate("el => window.getComputedStyle(el).display", nodes_div)
                print(f"   Display depois: {display_after}")
                
                # Contar ícones colapsados antes e depois
                colapsed_before = sum(1 for i in icons if page.query_selector(f"#{i.get_attribute('id').replace('ContentPlaceHolder1_ua_treeview', '').replace('i', '').replace('t', '')}_div_check") or True)
                
                # Melhor: contar quantos ícones têm display:none
                count_after = 0
                for ic in icons:
                    ic_id = ic.get_attribute('id')
                    nnum = ic_id.replace('ContentPlaceHolder1_ua_treeview', '').replace('i', '')
                    nnum = nnum.replace('t', '')
                    nid = f"ContentPlaceHolder1_ua_treeviewn{nnum}Nodes"
                    ndiv = page.query_selector(f"#{nid}")
                    if ndiv:
                        disp = page.evaluate("el => window.getComputedStyle(el).display", ndiv)
                        if disp == "none":
                            count_after += 1
                
                print(f"   Ícones colapsados após clique: {count_after}")
                break
    
    input("\nPressione Enter para fechar...")
    browser.close()
    
finally:
    p.stop()
