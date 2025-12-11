from playwright.sync_api import sync_playwright
import time
import json

def debug_expand_mechanism():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("[*] Acessando SICI...")
        page.goto("https://sici.rio.rj.gov.br/PAG/principal.aspx", wait_until="networkidle")
        print("[OK] Página carregada")
        
        # Coletar informações sobre a estrutura antes de qualquer ação
        print("\n[*] Analisando estrutura DOM...")
        structure_info = page.evaluate("""
            () => {
                let result = {
                    allLinks: [],
                    allIcons: [],
                    allContainers: [],
                    smsInfo: null
                };
                
                // Encontrar SMS
                let allLinks = document.querySelectorAll('a[id*="ua_treeview"]');
                for (let link of allLinks) {
                    if (link.innerText.trim() === 'SMS') {
                        result.smsInfo = {
                            id: link.id,
                            text: link.innerText.trim(),
                            parentHtml: link.parentElement.outerHTML.substring(0, 200)
                        };
                        
                        // Procurar ícone próximo
                        let parent = link.parentElement;
                        for (let i = 0; i < 3; i++) {
                            let icons = parent.querySelectorAll('img[src*="plus"]');
                            if (icons.length > 0) {
                                result.smsInfo.nearbyIcon = {
                                    id: icons[0].id,
                                    src: icons[0].src
                                };
                                break;
                            }
                            parent = parent.parentElement;
                        }
                    }
                }
                
                // Listar todos os ícones de expansão
                let allIcons = document.querySelectorAll('img[src*="plus"]');
                for (let icon of allIcons) {
                    result.allIcons.push({
                        id: icon.id,
                        src: icon.src.substring(icon.src.length - 30)
                    });
                }
                
                // Listar todos os containers
                let allContainers = document.querySelectorAll('[id*="Nodes"]');
                for (let cont of allContainers) {
                    let hasContent = cont.innerText.trim().length > 0;
                    if (cont.id.includes('31') || hasContent === false) {
                        result.allContainers.push({
                            id: cont.id,
                            hasContent: hasContent,
                            childCount: cont.querySelectorAll('a[id*="treeview"]').length
                        });
                    }
                }
                
                return result;
            }
        """)
        
        print(json.dumps(structure_info, indent=2, ensure_ascii=False))
        
        # Agora tentar clicar em SMS
        if structure_info['smsInfo']:
            sms_id = structure_info['smsInfo']['id']
            print(f"\n[*] Clicando em SMS: {sms_id}")
            page.evaluate(f"""
                (smsId) => {{
                    let el = document.getElementById(smsId);
                    if (el) el.click();
                }}
            """, sms_id)
            
            time.sleep(1)
            
            # Verificar mudanças
            print("\n[*] Analisando mudanças após clicar em SMS...")
            changes = page.evaluate("""
                () => {
                    let result = {
                        newIcons: [],
                        containersWithContent: []
                    };
                    
                    let allIcons = document.querySelectorAll('img[src*="plus"]');
                    for (let icon of allIcons) {
                        result.newIcons.push(icon.id);
                    }
                    
                    let containers = document.querySelectorAll('[id*="31Nodes"]');
                    for (let cont of containers) {
                        result.containersWithContent.push({
                            id: cont.id,
                            childCount: cont.querySelectorAll('a[id*="treeview"]').length,
                            visible: cont.offsetHeight > 0
                        });
                    }
                    
                    return result;
                }
            """)
            
            print(json.dumps(changes, indent=2, ensure_ascii=False))
            
            # Tentar expandir usando o ícone se encontrado
            if structure_info['smsInfo'].get('nearbyIcon'):
                icon_id = structure_info['smsInfo']['nearbyIcon']['id']
                print(f"\n[*] Tentando clicar no ícone: {icon_id}")
                page.evaluate(f"""
                    (iconId) => {{
                        let el = document.getElementById(iconId);
                        if (el) {{
                            console.log('Ícone encontrado, clicando...');
                            el.click();
                        }} else {{
                            console.log('Ícone não encontrado:', iconId);
                        }}
                    }}
                """, icon_id)
                
                time.sleep(1)
                
                # Verificar se filhos aparecem
                print("\n[*] Analisando após clicar no ícone...")
                final_check = page.evaluate("""
                    () => {
                        let containers = document.querySelectorAll('[id*="31Nodes"]');
                        let result = [];
                        
                        for (let cont of containers) {
                            let children = cont.querySelectorAll('a[id*="treeview"]');
                            result.push({
                                container: cont.id,
                                childCount: children.length,
                                childrenList: Array.from(children).map(c => c.innerText.trim())
                            });
                        }
                        
                        return result;
                    }
                """)
                
                print(json.dumps(final_check, indent=2, ensure_ascii=False))
        
        print("\n[*] Análise concluída. Navegador permanece aberto.")
        input("Pressione Enter para fechar...")
        browser.close()

if __name__ == "__main__":
    debug_expand_mechanism()
