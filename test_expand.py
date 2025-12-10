"""
Script para testar cliques e expansão de nós no TreeView SICI.
"""
from playwright.sync_api import sync_playwright

p = sync_playwright().start()
try:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    print("📄 Acessando site SICI...")
    page.goto('https://sici.rio.rj.gov.br/PAG/principal.aspx', wait_until='networkidle')
    page.wait_for_timeout(2000)
    
    # Buscar ícones expandíveis
    icons = page.query_selector_all("a[id*='ua_treeview'][id$='i']")
    print(f"\n🔍 Encontrados {len(icons)} ícones expandíveis")
    
    # Listar alguns
    print("\nPrimeiros 10 ícones:")
    for i, icon in enumerate(icons[:10]):
        icon_id = icon.get_attribute('id')
        node_num = icon_id.replace('ContentPlaceHolder1_ua_treeview', '').replace('i', '')
        nodes_id = f"ContentPlaceHolder1_ua_treeview{node_num}Nodes"
        nodes_div = page.query_selector(f"#{nodes_id}")
        
        if nodes_div:
            display = page.evaluate("el => window.getComputedStyle(el).display", nodes_div)
            print(f"  {i+1}. {icon_id} -> div={nodes_id}, display={display}")
        else:
            print(f"  {i+1}. {icon_id} -> SEM DIV")
    
    # Tentar clicar no primeiro ícone
    if icons:
        print("\n🖱️ Tentando clicar no primeiro ícone...")
        first_icon = icons[0]
        first_icon_id = first_icon.get_attribute('id')
        
        print(f"   ID: {first_icon_id}")
        print(f"   Text Content: {first_icon.text_content()}")
        
        first_icon.scroll_into_view_if_needed()
        first_icon.click()
        page.wait_for_timeout(1000)
        
        # Verificar se expandiu
        node_num = first_icon_id.replace('ContentPlaceHolder1_ua_treeview', '').replace('i', '')
        nodes_id = f"ContentPlaceHolder1_ua_treeview{node_num}Nodes"
        nodes_div = page.query_selector(f"#{nodes_id}")
        
        if nodes_div:
            display_after = page.evaluate("el => window.getComputedStyle(el).display", nodes_div)
            print(f"   Após clique: display={display_after}")
        
        # Contar nós agora
        all_nodes_after = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
        print(f"   Nós após clique: {len(all_nodes_after)}")
    
    input("\nPressione Enter para fechar...")
    browser.close()
    
finally:
    p.stop()
