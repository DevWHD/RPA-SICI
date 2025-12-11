from playwright.sync_api import sync_playwright
import time
import json

def debug_sms_structure():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("[*] Acessando SICI...")
        page.goto("https://sici.rio.rj.gov.br/PAG/principal.aspx", wait_until="networkidle")
        print("[OK] Página carregada\n")
        
        # Inspecionar a estrutura HTML do SMS
        print("[*] Inspecionando estrutura do SMS...")
        structure = page.evaluate("""
            () => {
                let links = document.querySelectorAll('a[id*="ua_treeview"]');
                for (let link of links) {
                    if (link.innerText.trim() === 'SMS') {
                        let parent = link.parentElement;
                        let grandparent = parent.parentElement;
                        
                        return {
                            link_html: link.outerHTML.substring(0, 200),
                            link_classes: link.className,
                            parent_tagName: parent.tagName,
                            parent_classes: parent.className,
                            parent_html: parent.outerHTML.substring(0, 300),
                            grandparent_tagName: grandparent.tagName,
                            grandparent_classes: grandparent.className,
                            grandparent_html: grandparent.outerHTML.substring(0, 500),
                            // Procurar elementos clicáveis próximos
                            siblings: Array.from(parent.children).map(c => ({
                                tag: c.tagName,
                                id: c.id,
                                class: c.className,
                                onclick: c.getAttribute('onclick'),
                                cursor: window.getComputedStyle(c).cursor
                            }))
                        };
                    }
                }
                return { error: 'SMS não encontrado' };
            }
        """)
        
        print(json.dumps(structure, indent=2, ensure_ascii=False))
        
        # Procurar elementos antes do link SMS
        print("\n[*] Procurando elemento '+' antes do link SMS...")
        before_link = page.evaluate("""
            () => {
                let result = {
                    sms_link_id: null,
                    previousElements: []
                };
                
                let links = document.querySelectorAll('a[id*="ua_treeview"]');
                for (let link of links) {
                    if (link.innerText.trim() === 'SMS') {
                        result.sms_link_id = link.id;
                        
                        // Procurar elementos antes (previousElementSibling)
                        let prev = link.previousElementSibling;
                        while (prev && result.previousElements.length < 3) {
                            result.previousElements.push({
                                tag: prev.tagName,
                                id: prev.id,
                                class: prev.className,
                                text: prev.innerText ? prev.innerText.substring(0, 20) : null,
                                html: prev.outerHTML.substring(0, 100)
                            });
                            prev = prev.previousElementSibling;
                        }
                        
                        // Procurar dentro do parent e encontrar todos os filhos
                        let parent = link.parentElement;
                        result.allParentChildren = [];
                        for (let i = 0; i < parent.children.length; i++) {
                            let child = parent.children[i];
                            result.allParentChildren.push({
                                index: i,
                                tag: child.tagName,
                                id: child.id,
                                class: child.className,
                                text: child.innerText ? child.innerText.substring(0, 15) : null
                            });
                        }
                        break;
                    }
                }
                return result;
            }
        """)
        
        print(json.dumps(before_link, indent=2, ensure_ascii=False))
        
        print("\n[*] Navegador permanece aberto. Pressione Enter para fechar...")
        input()
        browser.close()

if __name__ == "__main__":
    debug_sms_structure()
