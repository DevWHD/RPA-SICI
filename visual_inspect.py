"""Verificar visualmente a estrutura do SMS."""

from playwright.sync_api import sync_playwright
from src.config import BASE_URL

print("Abrindo navegador para inspeção visual...")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.viewport = {"width": 1200, "height": 800}
    
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(2000)
    
    # Encontrar e expandir SMS
    sms_links = page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
    for link in sms_links:
        text = link.text_content().strip()
        if text == "SMS":
            sms_id = link.get_attribute('id')
            sms_num = sms_id.replace('ContentPlaceHolder1_ua_treeviewt', '')
            sms_icon_id = f"ContentPlaceHolder1_ua_treeviewt{sms_num}i"
            
            # Expandir clicando no ícone
            sms_icon = page.query_selector(f"#{sms_icon_id}")
            if sms_icon:
                sms_icon.click()
                page.wait_for_timeout(1000)
            
            # Highlight do SMS
            page.evaluate("""
                (id) => {
                    let el = document.getElementById(id);
                    if (el) {
                        el.style.backgroundColor = 'yellow';
                        el.scrollIntoView({behavior: 'smooth'});
                    }
                }
            """, sms_id)
            
            break
    
    print("✓ SMS expandido e destaca em amarelo")
    print("Clique no SMS (texto) para carregar mais informações...")
    print("Pressione ENTER para fechar o navegador...")
    input()
    browser.close()
