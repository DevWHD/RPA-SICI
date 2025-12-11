from playwright.sync_api import sync_playwright
import time
import json

def debug_children_after_click():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("[*] Acessando SICI...")
        page.goto("https://sici.rio.rj.gov.br/PAG/principal.aspx", wait_until="networkidle")
        print("[OK] Página carregada\n")
        
        # Encontrar e clicar em SMS
        print("[*] Clicando em SMS...")
        page.evaluate("""
            () => {
                let links = document.querySelectorAll('a[id*="ua_treeview"]');
                for (let link of links) {
                    if (link.innerText.trim() === 'SMS') {
                        link.click();
                        break;
                    }
                }
            }
        """)
        
        # Aguardar postback
        time.sleep(3)
        print("[OK] SMS clicado\n")
        
        # Investigar a estrutura
        result = page.evaluate("""
            () => {
                let info = {
                    smsId: null,
                    containerId: null,
                    containerStatus: {},
                    children: [],
                    allContainersWithN31: []
                };
                
                // Encontrar SMS
                let links = document.querySelectorAll('a[id*="ua_treeview"]');
                for (let link of links) {
                    if (link.innerText.trim() === 'SMS') {
                        info.smsId = link.id;
                        
                        // Extrair o número (31)
                        let match = link.id.match(/t(\\d+)$/);
                        if (match) {
                            let num = match[1];
                            
                            // Procurar o container esperado
                            let expectedContainerId = 'ContentPlaceHolder1_ua_treeviewn' + num + 'Nodes';
                            info.containerId = expectedContainerId;
                            let container = document.getElementById(expectedContainerId);
                            
                            if (container) {
                                info.containerStatus = {
                                    found: true,
                                    display: window.getComputedStyle(container).display,
                                    visibility: window.getComputedStyle(container).visibility,
                                    visible: container.offsetHeight > 0,
                                    innerTextLength: container.innerText.length,
                                    innerHTML_length: container.innerHTML.length,
                                    childNodeCount: container.childNodes.length,
                                    tableCount: container.querySelectorAll('table').length,
                                    linkCount: container.querySelectorAll('a[id*="treeview"]').length
                                };
                                
                                // Listar todos os 'a' dentro
                                let allLinks = container.querySelectorAll('a[id*="treeview"]');
                                for (let a of allLinks) {
                                    let text = a.innerText.trim();
                                    info.children.push({
                                        id: a.id,
                                        text: text,
                                        visible: a.offsetHeight > 0
                                    });
                                }
                            } else {
                                info.containerStatus.found = false;
                                info.containerStatus.msg = 'Container não encontrado';
                            }
                        }
                        break;
                    }
                }
                
                // Listar TODOS os containers que contêm "31" no ID
                let allContainers = document.querySelectorAll('[id*="31"]');
                for (let cont of allContainers) {
                    if (cont.id && cont.id.includes('Node')) {
                        info.allContainersWithN31.push({
                            id: cont.id,
                            tagName: cont.tagName,
                            childCount: cont.querySelectorAll('a').length,
                            visible: cont.offsetHeight > 0
                        });
                    }
                }
                
                return info;
            }
        """)
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        print("\n[*] Navegador permanece aberto. Pressione Enter para fechar...")
        input()
        browser.close()

if __name__ == "__main__":
    debug_children_after_click()
