from playwright.sync_api import sync_playwright
import time
import json

def debug_expand_icon():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("[*] Acessando SICI...")
        page.goto("https://sici.rio.rj.gov.br/PAG/principal.aspx", wait_until="networkidle")
        print("[OK] Página carregada\n")
        
        # PASSO 1: Procurar ícone de expandir ANTES de clicar
        print("[*] ANTES de clicar em SMS:")
        before_click = page.evaluate("""
            () => {
                let info = {
                    expandIconsTotal: 0,
                    expandIconsWithText31: 0,
                    icons: []
                };
                
                let allIcons = document.querySelectorAll('img');
                for (let icon of allIcons) {
                    if (icon.src && (icon.src.includes('plus') || icon.src.includes('minus') || icon.src.includes('expand'))) {
                        info.expandIconsTotal++;
                        let iconInfo = {
                            id: icon.id,
                            src: icon.src.substring(icon.src.length - 40),
                            alt: icon.alt,
                            parent_id: icon.parentElement ? icon.parentElement.id : null
                        };
                        info.icons.push(iconInfo);
                        
                        if (icon.id && icon.id.includes('31')) {
                            info.expandIconsWithText31++;
                        }
                    }
                }
                
                return info;
            }
        """)
        print(json.dumps(before_click, indent=2, ensure_ascii=False))
        
        # PASSO 2: Clicar em SMS
        print("\n[*] Clicando em SMS...")
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
        
        # Aguardar mais tempo
        time.sleep(4)
        print("[OK] SMS clicado\n")
        
        # PASSO 3: Procurar ícone de expandir DEPOIS de clicar
        print("[*] DEPOIS de clicar em SMS:")
        after_click = page.evaluate("""
            () => {
                let info = {
                    expandIconsTotal: 0,
                    expandIconsWithText31: 0,
                    expandIconFor31: null,
                    icons: []
                };
                
                let allIcons = document.querySelectorAll('img');
                for (let icon of allIcons) {
                    if (icon.src && (icon.src.includes('plus') || icon.src.includes('minus') || icon.src.includes('expand'))) {
                        info.expandIconsTotal++;
                        let iconInfo = {
                            id: icon.id,
                            src: icon.src.substring(icon.src.length - 40),
                            alt: icon.alt,
                            visible: icon.offsetHeight > 0
                        };
                        info.icons.push(iconInfo);
                        
                        if (icon.id && icon.id.includes('31')) {
                            info.expandIconsWithText31++;
                            info.expandIconFor31 = icon.id;
                        }
                    }
                }
                
                return info;
            }
        """)
        print(json.dumps(after_click, indent=2, ensure_ascii=False))
        
        # PASSO 4: Se encontrou ícone, tentar clicar nele
        if after_click['expandIconFor31']:
            print(f"\n[*] Encontrado ícone de expansão: {after_click['expandIconFor31']}")
            print("[*] Clicando no ícone...")
            
            page.evaluate(f"""
                (iconId) => {{
                    let icon = document.getElementById(iconId);
                    if (icon) {{
                        console.log('Clicando em:', icon.id);
                        icon.click();
                    }}
                }}
            """, after_click['expandIconFor31'])
            
            time.sleep(2)
            
            # Verificar filhos após clicar no ícone
            final_check = page.evaluate("""
                () => {
                    let container = document.getElementById('ContentPlaceHolder1_ua_treeviewn31Nodes');
                    if (!container) return { error: 'Container não encontrado' };
                    
                    let allLinks = container.querySelectorAll('a[id*="treeview"]');
                    let children = [];
                    for (let link of allLinks) {
                        let text = link.innerText.trim();
                        if (text && text !== '0') {
                            children.push({
                                id: link.id,
                                text: text
                            });
                        }
                    }
                    
                    return {
                        containerVisible: container.offsetHeight > 0,
                        display: window.getComputedStyle(container).display,
                        childrenCount: children.length,
                        children: children
                    };
                }
            """)
            
            print("\n[*] DEPOIS de clicar no ícone de expansão:")
            print(json.dumps(final_check, indent=2, ensure_ascii=False))
        
        print("\n[*] Navegador permanece aberto. Pressione Enter para fechar...")
        input()
        browser.close()

if __name__ == "__main__":
    debug_expand_icon()
