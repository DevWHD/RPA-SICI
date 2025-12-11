from playwright.sync_api import sync_playwright
import time
import json

def check_initial_children():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("[*] Acessando SICI...")
        page.goto("https://sici.rio.rj.gov.br/PAG/principal.aspx", wait_until="networkidle")
        print("[OK] Página carregada")
        
        # Imediatamente após carregar, verificar filhos de SMS
        print("\n[*] Verificando filhos de SMS na página inicial (sem clicar)...")
        initial_children = page.evaluate("""
            () => {
                let result = {
                    smsFound: false,
                    children: [],
                    containerInfo: {}
                };
                
                // Encontrar SMS
                let allLinks = document.querySelectorAll('a[id*="ua_treeview"]');
                for (let link of allLinks) {
                    if (link.innerText.trim() === 'SMS') {
                        result.smsFound = true;
                        let smsId = link.id;
                        let match = smsId.match(/t(\\d+)$/);
                        if (match) {
                            let nodeNum = match[1];
                            let containerId = 'ContentPlaceHolder1_ua_treeviewn' + nodeNum + 'Nodes';
                            let container = document.getElementById(containerId);
                            
                            if (container) {
                                result.containerInfo = {
                                    id: containerId,
                                    visible: container.offsetHeight > 0,
                                    display: window.getComputedStyle(container).display,
                                    innerHTML_length: container.innerHTML.length,
                                    childNodes: container.childNodes.length
                                };
                                
                                // Buscar todos os 'a' dentro do container
                                let childLinks = container.querySelectorAll('a[id*="treeview"]');
                                for (let childLink of childLinks) {
                                    let text = childLink.innerText.trim();
                                    if (text && text !== '0') {
                                        result.children.push({
                                            id: childLink.id,
                                            text: text
                                        });
                                    }
                                }
                            }
                        }
                        break;
                    }
                }
                
                return result;
            }
        """)
        
        print(json.dumps(initial_children, indent=2, ensure_ascii=False))
        
        print("\n[*] Analisando ALL containers Nodes no DOM...")
        all_containers_with_children = page.evaluate("""
            () => {
                let result = [];
                let allContainers = document.querySelectorAll('[id*="Nodes"]');
                
                for (let container of allContainers) {
                    let childLinks = container.querySelectorAll(':scope a[id*="treeview"]');
                    if (childLinks.length > 0) {
                        let children = [];
                        for (let link of childLinks) {
                            children.push(link.innerText.trim());
                        }
                        result.push({
                            container: container.id,
                            childCount: childLinks.length,
                            children: children.slice(0, 3)  // Primeiros 3 só para debug
                        });
                    }
                }
                
                return result;
            }
        """)
        
        print("Containers com filhos:")
        print(json.dumps(all_containers_with_children, indent=2, ensure_ascii=False))
        
        print("\n[*] Navegador permanece aberto. Pressione Enter para fechar...")
        input()
        browser.close()

if __name__ == "__main__":
    check_initial_children()
