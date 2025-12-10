"""
Script de diagnóstico para entender a estrutura HTML do site SICI.
"""
from playwright.sync_api import sync_playwright

p = sync_playwright().start()
try:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    print("📄 Acessando site SICI...")
    page.goto('https://sici.rio.rj.gov.br/PAG/principal.aspx', wait_until='networkidle')
    page.wait_for_timeout(3000)
    
    # Coletar informações
    print("\n📊 Diagnóstico encontrado:")
    print(f"  imagens_plus: {len(page.query_selector_all('img[src*=plus]'))}")
    print(f"  imagens_minus: {len(page.query_selector_all('img[src*=minus]'))}")
    print(f"  imagens_spacer: {len(page.query_selector_all('img[src*=spacer]'))}")
    print(f"  total_imagens: {len(page.query_selector_all('img'))}")
    print(f"  tables: {len(page.query_selector_all('table'))}")
    print(f"  ul_elements: {len(page.query_selector_all('ul'))}")
    print(f"  li_elements: {len(page.query_selector_all('li'))}")
    
    # Verificar se há TreeView
    treeview = page.query_selector("div[id*='TreeView'],table[id*='TreeView']")
    print(f"  TreeView encontrado: {treeview is not None}")
    
    # Tentar extrair alguns IDs
    print("\n🔍 IDs encontrados na página (primeiros 15):")
    all_ids = page.query_selector_all("[id]")
    for i, elem in enumerate(all_ids[:15]):
        id_attr = elem.get_attribute('id')
        tag = page.evaluate('(el) => el.tagName', elem)
        print(f"  {i+1}. {id_attr} ({tag})")
    
    # Verificar conteúdo do ContentPlaceHolder
    content = page.query_selector("[id*='ContentPlaceHolder']")
    if content:
        print(f"\n✅ ContentPlaceHolder encontrado")
        rows = content.query_selector_all("tr")
        print(f"  - TR dentro: {len(rows)}")
        divs = content.query_selector_all("div")
        print(f"  - DIV dentro: {len(divs)}")
    
    browser.close()
    print("\n✅ Diagnóstico concluído!")
finally:
    p.stop()
