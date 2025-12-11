from playwright.sync_api import sync_playwright
import time
import json

def debug_sms_click_and_data():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("[*] Acessando SICI...")
        page.goto("https://sici.rio.rj.gov.br/PAG/principal.aspx", wait_until="networkidle")
        print("[OK] Página carregada\n")
        
        # Encontrar SMS e capturar seu ID e posição
        sms_info = page.evaluate("""
            () => {
                let links = document.querySelectorAll('a[id*="ua_treeview"]');
                for (let link of links) {
                    if (link.innerText.trim() === 'SMS') {
                        let rect = link.getBoundingClientRect();
                        return {
                            id: link.id,
                            text: link.innerText.trim(),
                            class: link.className,
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        };
                    }
                }
                return null;
            }
        """)
        
        print("[*] SMS encontrado:")
        print(json.dumps(sms_info, indent=2))
        
        # Clicar em SMS
        print("\n[*] Clicando em SMS...")
        page.click(f"#{sms_info['id']}")
        time.sleep(2)
        
        # Verificar qual nó está selecionado após o click
        print("\n[*] Verificando qual nó está selecionado após clicar...")
        selected = page.evaluate("""
            () => {
                let allLinks = document.querySelectorAll('a[id*="ua_treeview"]');
                for (let link of allLinks) {
                    if (link.className && link.className.includes('NodeSelecionado')) {
                        return {
                            id: link.id,
                            text: link.innerText.trim(),
                            className: link.className
                        };
                    }
                }
                return { msg: "Nenhum nó com classe NodeSelecionado" };
            }
        """)
        
        print(json.dumps(selected, indent=2))
        
        # Procurar pelo campo de "Titular" na página para ver qual órgão está sendo exibido
        print("\n[*] Verificando dados exibidos na página (procurando por 'Titular')...")
        page_data = page.evaluate("""
            () => {
                // Procurar pelo texto "Titular" e pegar o valor associado
                let allText = document.body.innerText;
                let lines = allText.split('\\n');
                
                let result = {
                    foundTitular: false,
                    titularLine: null,
                    titularValue: null,
                    cargoLine: null,
                    cargoValue: null,
                    pageTitle: document.title,
                    dropdownValue: null
                };
                
                // Procurar dropdown "Informações Gerais"
                let dropdown = document.querySelector('select');
                if (dropdown) {
                    result.dropdownValue = dropdown.value;
                    result.dropdownText = dropdown.selectedOptions[0].text;
                }
                
                // Procurar por "Titular" e "Cargo"
                for (let i = 0; i < lines.length; i++) {
                    if (lines[i].includes('Titular')) {
                        result.foundTitular = true;
                        result.titularLine = lines[i];
                        if (i + 1 < lines.length) {
                            result.titularValue = lines[i + 1];
                        }
                    }
                    if (lines[i].includes('Cargo')) {
                        result.cargoLine = lines[i];
                        if (i + 1 < lines.length) {
                            result.cargoValue = lines[i + 1];
                        }
                    }
                }
                
                return result;
            }
        """)
        
        print(json.dumps(page_data, indent=2, ensure_ascii=False))
        
        # Verificar a URL e o estado da página
        print(f"\n[*] URL atual: {page.url}")
        print(f"[*] Título da página: {page.title()}")
        
        print("\n[*] Navegador permanece aberto. Pressione Enter para fechar...")
        input()
        browser.close()

if __name__ == "__main__":
    debug_sms_click_and_data()
