"""
Script para inspecionar o HTML do site SICI e encontrar os seletores corretos.
"""
from playwright.sync_api import sync_playwright

with sync_playwright().start() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    print("📄 Acessando site SICI...")
    page.goto('https://sici.rio.rj.gov.br/PAG/principal.aspx', wait_until='networkidle')
    page.wait_for_timeout(3000)
    
    # Procurar por diferentes seletores
    print("\n🔍 Buscando estruturas da árvore...")
    
    # Verificar TreeView
    treeview = page.query_selector("#ctl00_ContentPlac
                                   eHolder1_TreeView1")
    print(f"TreeView por ID: {treeview is not None}")
    
    # Procurar por imagens com 'plus'
    plus_images = page.query_selector_all("img[src*='plus']")
    print(f"Imagens com 'plus': {len(plus_images)}")
    
    # Procurar por divs com classe 'tree' ou 'treeview'
    divs_tree = page.query_selector_all("div[class*='tree'], div[class*='TreeView']")
    print(f"Divs com 'tree' ou 'TreeView': {len(divs_tree)}")
    
    # Procurar por ul/li (árvore comum)
    ul_elements = page.query_selector_all("ul")
    print(f"Elementos UL encontrados: {len(ul_elements)}")
    
    # Procurar por todas as imagens
    all_images = page.query_selector_all("img")
    print(f"Total de imagens: {len(all_images)}")
    
    # Listar alguns srcs de imagens para entender o padrão
    print("\n📸 Alguns srcs de imagens encontradas:")
    for i, img in enumerate(all_images[:10]):
        src = img.get_attribute('src')
        alt = img.get_attribute('alt')
        print(f"  {i+1}. src={src}, alt={alt}")
    
    # Procurar por spans com classe comum de nós
    spans = page.query_selector_all("span[class*='Node']")
    print(f"\nSpans com 'Node': {len(spans)}")
    
    # Se encontrar nós, listar alguns
    if spans:
        print("Alguns nós encontrados:")
        for i, span in enumerate(spans[:5]):
            text = span.text_content()
            print(f"  {i+1}. {text}")
    
    browser.close()
    print("\n✅ Inspeção concluída. Verifique o navegador que se abriu.")
