"""
Script avançado para explorar o TreeView do SICI.
"""
from playwright.sync_api import sync_playwright

p = sync_playwright().start()
try:
    browser = p.chromium.launch(headless=False)  # Abrir navegador para visualizar
    context = browser.new_context()
    page = context.new_page()
    
    print("📄 Acessando site SICI...")
    page.goto('https://sici.rio.rj.gov.br/PAG/principal.aspx', wait_until='networkidle')
    page.wait_for_timeout(3000)
    
    # Procurar pelo TreeView
    print("\n🔍 Procurando elementos do TreeView...")
    
    # Buscar por elementos com "ua_treeview" no id
    ua_elements = page.query_selector_all("[id*='ua_treeview']")
    print(f"Elementos 'ua_treeview' encontrados: {len(ua_elements)}")
    for elem in ua_elements:
        id_attr = elem.get_attribute('id')
        tag = page.evaluate('(el) => el.tagName', elem)
        print(f"  - {id_attr} ({tag})")
    
    # Procurar em toda a página por estruturas de árvore comuns
    print("\n🌳 Estruturas possíveis:")
    
    # Verificar por <li> com click handlers
    all_spans = page.query_selector_all("span")
    print(f"Total de spans: {len(all_spans)}")
    
    # Tentar clicar em algo que pareça um + para expandir
    clickable = page.query_selector_all("span[onclick],a[onclick],img[onclick]")
    print(f"Elementos com onclick: {len(clickable)}")
    
    # Procurar por divs com classes que sugiram nós
    node_divs = page.query_selector_all("div[class*='node'],div[class*='Node'],div[class*='tree'],div[class*='Tree']")
    print(f"Divs com 'node' ou 'tree' no class: {len(node_divs)}")
    
    # Tentar encontrar o container principal do TreeView
    print("\n📦 Buscando container da árvore:")
    containers = page.query_selector_all("div[class*='tree'],div[class*='Tree'],div[id*='tree'],div[id*='Tree']")
    for i, cont in enumerate(containers[:5]):
        id_attr = cont.get_attribute('id')
        cls = cont.get_attribute('class')
        print(f"  {i+1}. id={id_attr}, class={cls}")
        
        # Verificar o que tem dentro
        children = page.query_selector_all("div", cont)
        print(f"       - {len(page.query_selector_all('div', cont))} divs dentro")
    
    # Procurar por elementos que podem ter sido carregados dinamicamente
    print("\n⚡ Verificando se há conteúdo carregado dinamicamente:")
    
    # Procurar por qualquer elemento com texto "SMS"
    all_elements = page.query_selector_all("*")
    sms_count = 0
    for elem in all_elements:
        if "SMS" in (elem.text_content() or ""):
            sms_count += 1
            tag = page.evaluate('(el) => el.tagName', elem)
            text = elem.text_content()[:50]
            print(f"  Encontrado em {tag}: {text}")
            if sms_count >= 3:
                break
    
    if sms_count == 0:
        print("  ❌ Nenhum texto 'SMS' encontrado")
    
    # Tentar expandir clicando em qualquer coisa que pareça ser um botão de expandir
    print("\n🖱️ Tentando clicar em elementos expandíveis...")
    
    # Procurar por spans que possam ser clicáveis
    all_clicks = page.query_selector_all("span,a,div")
    for i, elem in enumerate(all_clicks[:10]):
        onclick = elem.get_attribute('onclick')
        if onclick and 'Expand' in onclick:
            print(f"  Encontrado: {elem.text_content()[:30]} -> {onclick[:50]}")
    
    print("\n✅ Exploração concluída! O navegador permanecerá aberto para análise manual.")
    print("   Você pode inspecionar os elementos no navegador (F12) para encontrar a estrutura correta.")
    
    input("Pressione Enter para fechar o navegador...")
    
    browser.close()
    
finally:
    p.stop()
