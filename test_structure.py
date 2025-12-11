"""
Script de teste para inspecionar a estrutura HTML da pagina SICI
e entender como os dados estao organizados.
"""

from playwright.sync_api import sync_playwright
from src.config import BASE_URL, HEADLESS

def test_page_structure():
    """Inspeciona a estrutura da pagina de um no especifico"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()
        
        # Acessar site
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        
        # Encontrar e expandir SMS
        try:
            sms_link = page.query_selector("a[id*='0i']")
            if sms_link:
                print("[+] Clicando no SMS...")
                sms_link.click()
                page.wait_for_timeout(1000)
                
                # Encontrar primeiro filho
                children_div = page.query_selector("div[id*='0Nodes']")
                if children_div:
                    print("[+] Encontrado div de filhos, expandindo...")
                    page.evaluate("""
                        () => {
                            var elem = document.querySelector("div[id*='0Nodes']");
                            if (elem) elem.style.display = "block";
                        }
                    """)
                    page.wait_for_timeout(500)
                    
                    # Encontrar primeiro filho
                    links = page.query_selector_all("a[id*='i']")
                    if len(links) > 1:
                        first_child = links[1]
                        child_text = first_child.text_content().strip()
                        print(f"[+] Clicando no primeiro filho: {child_text}")
                        first_child.click()
                        page.wait_for_timeout(2000)
                        
                        # INSPECIONAR A ESTRUTURA HTML
                        print("\n" + "="*80)
                        print("ESTRUTURA HTML COMPLETA DA PAGINA:")
                        print("="*80)
                        
                        html = page.content()
                        print(html)
                        
                        # Salvar para arquivo
                        with open("page_structure.html", "w", encoding="utf-8") as f:
                            f.write(html)
                        print("\n[+] HTML salvo em page_structure.html")
                        
                        # INSPECIONAR TEXTO
                        print("\n" + "="*80)
                        print("TEXTO EXTRAIDO COM INNERTEXT:")
                        print("="*80)
                        
                        text = page.evaluate("() => document.body.innerText")
                        print(text)
                        
                        # Salvar para arquivo
                        with open("page_text.txt", "w", encoding="utf-8") as f:
                            f.write(text)
                        print("\n[+] Texto salvo em page_text.txt")
                        
        except Exception as e:
            print(f"[-] Erro: {e}")
            import traceback
            traceback.print_exc()
        
        browser.close()

if __name__ == "__main__":
    test_page_structure()
