"""
Script para mapear a estrutura real do TreeView SICI.
"""
from playwright.sync_api import sync_playwright

p = sync_playwright().start()
try:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    print("📄 Acessando site SICI...")
    page.goto('https://sici.rio.rj.gov.br/PAG/principal.aspx', wait_until='networkidle')
    page.wait_for_timeout(2000)
    
    # Buscar todos os elementos do TreeView
    all_treeview_elements = page.query_selector_all("[id*='ua_treeview']")
    print(f"\n🔍 Total de elementos ua_treeview: {len(all_treeview_elements)}")
    
    # Organizar por tipo
    icons = []
    nodes = []
    containers = []
    
    for elem in all_treeview_elements:
        elem_id = elem.get_attribute('id')
        tag = page.evaluate('(el) => el.tagName', elem)
        
        if elem_id.endswith('i'):
            icons.append((elem_id, tag))
        elif 'Nodes' in elem_id:
            containers.append((elem_id, tag))
        else:
            nodes.append((elem_id, tag))
    
    print(f"\n📌 Ícones (terminam em 'i'): {len(icons)}")
    print(f"📌 Nós (sem 'i'): {len(nodes)}")
    print(f"📌 Containers (com 'Nodes'): {len(containers)}")
    
    # Mostrar alguns exemplos de cada tipo
    print("\nExemplos de ícones:")
    for icon_id, tag in icons[:5]:
        print(f"  {icon_id} ({tag})")
    
    print("\nExemplos de nós:")
    for node_id, tag in nodes[:5]:
        print(f"  {node_id} ({tag})")
    
    print("\nExemplos de containers:")
    for cont_id, tag in containers[:5]:
        print(f"  {cont_id} ({tag})")
    
    # Agora vamos tentar entender a relação entre ícone e container
    # Um ícone t0i provavelmente corresponde a um container t0Nodes ou similar
    
    if icons and containers:
        print("\n🔗 Mapeando relações:")
        first_icon_id = icons[0][0]  # ex: ContentPlaceHolder1_ua_treeviewt0i
        print(f"  Ícone: {first_icon_id}")
        
        # Extrair o número
        # Tentar padrões comuns
        patterns_to_try = [
            first_icon_id.replace('i', 'Nodes'),  # t0i -> t0Nodes
            first_icon_id.replace('i', 'nNodes'),  # t0i -> t0nNodes
            first_icon_id.replace('_i', '_nNodes'),  # ...
        ]
        
        for pattern in patterns_to_try:
            matching = [c for c in containers if c[0] == pattern]
            if matching:
                print(f"  ✅ Encontrado: {pattern}")
            else:
                # Procurar algo semelhante
                similar = [c for c in containers if pattern.split('treeview')[1].split('N')[0] in c[0]]
                if similar:
                    print(f"  Similar a {pattern}: {similar[0][0]}")
    
    browser.close()
    
finally:
    p.stop()
