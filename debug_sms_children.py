from playwright.sync_api import sync_playwright
import time

def debug_sms_children():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("[*] Acessando SICI...")
        page.goto("https://sici.rio.rj.gov.br/PAG/principal.aspx", wait_until="networkidle")
        print("[OK] Página carregada")
        
        # Encontrar SMS
        print("\n[*] Procurando SMS...")
        sms_id = page.evaluate("""
            () => {
                let allLinks = document.querySelectorAll('a[id*="ua_treeview"]');
                for (let link of allLinks) {
                    if (link.innerText.trim() === 'SMS') {
                        return link.id;
                    }
                }
                return null;
            }
        """)
        
        if not sms_id:
            print("[!] SMS não encontrado")
            browser.close()
            return
            
        print(f"[OK] SMS encontrado: {sms_id}")
        
        # PRIMEIRO: Clicar no SMS para selecioná-lo
        print("\n[*] Clicando em SMS para selecioná-lo...")
        page.evaluate(f"""
            (smsId) => {{
                let el = document.getElementById(smsId);
                if (el) el.click();
            }}
        """, sms_id)
        
        import time
        time.sleep(1)
        print("[OK] SMS clicado")
        
        # DEPOIS: Verificar se SMS tem ícone de expandir - buscar todos os ícones de expansão
        print("\n[*] Verificando ícone de expandir...")
        expand_info = page.evaluate(f"""
            (smsId) => {{
                // Encontrar todos os ícones de expansão
                let allIcons = document.querySelectorAll('img[src*="plus"]');
                console.log('Total de ícones de expansão:', allIcons.length);
                
                let result = {{
                    found: false,
                    iconId: null,
                    src: null,
                    allIcons: []
                }};
                
                // Procurar o ícone relacionado ao SMS
                let smsIcons = Array.from(allIcons).filter(img => img.id.includes('31'));
                console.log('Ícones com "31":', smsIcons.length);
                
                for (let img of allIcons) {{
                    result.allIcons.push({{id: img.id, src: img.src}});
                }}
                
                // Tentar encontrar usando o padrão do HTML
                let expandIcon = null;
                for (let img of allIcons) {{
                    if (img.id.includes('31') && img.src.includes('plus')) {{
                        expandIcon = img;
                        break;
                    }}
                }}
                
                result.found = expandIcon !== null;
                result.iconId = expandIcon ? expandIcon.id : null;
                result.src = expandIcon ? expandIcon.src : null;
                
                return result;
            }}
        """, sms_id)
        
        print(f"[DEBUG] Ícone de expandir: Found={expand_info['found']}, ID={expand_info['iconId']}")
        print(f"[DEBUG] Total de ícones no DOM: {len(expand_info['allIcons'])}")
        for icon in expand_info['allIcons']:
            print(f"  - {icon['id']}")
        
        # Se tem ícone, expandir
        if expand_info and expand_info['found']:
            print("\n[*] Expandindo SMS...")
            page.evaluate(f"""
                (iconId) => {{
                    let expandIcon = document.getElementById(iconId);
                    if (expandIcon) {{
                        console.log('Clicando em:', expandIcon.id);
                        expandIcon.click();
                    }}
                }}
            """, expand_info['iconId'])
            
            import time
            time.sleep(2)
            print("[OK] SMS expandido")
        
        # Buscar container de filhos
        print("\n[*] Buscando container de filhos...")
        children_info = page.evaluate(f"""
            (smsId) => {{
                // Converter para container ID
                let containerId = smsId.replace(/t(\\d+)$/, 'n$1Nodes');
                let container = document.getElementById(containerId);
                
                if (!container) {{
                    return {{found: false, msg: 'Container não encontrado'}};
                }}
                
                console.log('Container encontrado:', container.id);
                console.log('Container HTML length:', container.innerHTML.length);
                console.log('Container visível?', container.offsetHeight > 0);
                
                // Buscar filhos - tentar várias seletores
                let childLinks1 = container.querySelectorAll(':scope > table > tbody > tr > td > a[id*="treeview"]');
                console.log('Selector 1 (> table > tbody > tr > td > a):', childLinks1.length);
                
                let childLinks2 = container.querySelectorAll('a[id*="treeview"]');
                console.log('Selector 2 (all a):', childLinks2.length);
                
                let childLinks3 = container.querySelectorAll('table');
                console.log('Tables no container:', childLinks3.length);
                
                let childLinks4 = container.querySelectorAll('span');
                console.log('Spans no container:', childLinks4.length);
                
                // Coletar os filhos com o melhor selector
                let children = [];
                let childLinks = childLinks2.length > 0 ? childLinks2 : childLinks1;
                
                for (let link of childLinks) {{
                    let text = link.innerText.trim();
                    if (text && text !== '0') {{
                        children.push({{
                            id: link.id,
                            text: text
                        }});
                    }}
                }}
                
                return {{
                    found: true,
                    containerId: container.id,
                    childrenCount: children.length,
                    children: children
                }};
            }}
        """, sms_id)
        
        print("\n" + "="*60)
        print("RESULTADO:")
        print("="*60)
        import json
        print(json.dumps(children_info, indent=2, ensure_ascii=False))
        
        browser.close()

if __name__ == "__main__":
    debug_sms_children()
