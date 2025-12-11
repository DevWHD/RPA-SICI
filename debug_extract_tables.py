"""
Script de debug para visualizar a estrutura das tabelas no SICI
e testar a extração de dados.
"""
from playwright.sync_api import sync_playwright
import json
import time

def debug_tables():
    """Debuga a estrutura das tabelas e extração de dados."""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("\n[*] Acessando SICI...")
        page.goto("https://sici.rio.rj.gov.br/PAG/principal.aspx", timeout=60000)
        page.wait_for_timeout(3000)
        
        print("[*] Aguardando TreeView...")
        page.wait_for_selector("#ContentPlaceHolder1_ua_treeview", timeout=30000)
        
        print("[*] Procurando SMS...")
        sms_node = None
        nodes = page.query_selector_all("[id^='ContentPlaceHolder1_ua_treeviewt']")
        
        for node in nodes:
            text = node.text_content()
            if "SMS" in text and "Secretaria Municipal" in text:
                sms_node = node
                print(f"[OK] SMS encontrado: {text[:100]}")
                break
        
        if not sms_node:
            print("[!] SMS nao encontrado!")
            browser.close()
            return
        
        # Expandir SMS
        print("[*] Expandindo SMS...")
        try:
            expand_icon = sms_node.query_selector("img[src*='plus']")
            if expand_icon:
                expand_icon.click()
                page.wait_for_timeout(1000)
        except:
            pass
        
        # Clicar no SMS
        print("[*] Clicando no SMS...")
        sms_node.click()
        page.wait_for_timeout(2000)
        
        # Tentar clicar em Informações Gerais
        print("[*] Procurando 'Informações Gerais'...")
        try:
            info_gerais = page.query_selector_all("select option, a")
            for elem in info_gerais:
                text = elem.text_content().strip()
                if "Informações Gerais" in text or "Informacoes Gerais" in text:
                    print(f"[*] Clicando em: {text}")
                    elem.click()
                    page.wait_for_timeout(1000)
                    break
        except Exception as e:
            print(f"[!] Erro ao clicar em Informações Gerais: {e}")
        
        # Extrair estrutura das tabelas
        print("\n" + "="*60)
        print("ESTRUTURA DAS TABELAS")
        print("="*60)
        
        table_structure = page.evaluate("""
            () => {
                let result = {
                    tables: [],
                    raw_text: document.body.innerText
                };
                
                let tables = document.querySelectorAll('table');
                
                tables.forEach((table, tableIdx) => {
                    let tableInfo = {
                        index: tableIdx,
                        rows: []
                    };
                    
                    let rows = table.querySelectorAll('tr');
                    rows.forEach((row, rowIdx) => {
                        let cells = Array.from(row.querySelectorAll('td, th')).map(cell => {
                            return {
                                text: cell.innerText.trim(),
                                colspan: cell.colSpan || 1,
                                rowspan: cell.rowSpan || 1,
                                tagName: cell.tagName
                            };
                        });
                        
                        if (cells.length > 0) {
                            tableInfo.rows.push({
                                rowIndex: rowIdx,
                                cells: cells
                            });
                        }
                    });
                    
                    if (tableInfo.rows.length > 0) {
                        result.tables.push(tableInfo);
                    }
                });
                
                return result;
            }
        """)
        
        # Exibir estrutura
        for table in table_structure['tables']:
            print(f"\n--- TABELA {table['index']} ---")
            for row in table['rows']:
                print(f"  Linha {row['rowIndex']}:")
                for cell_idx, cell in enumerate(row['cells']):
                    print(f"    Celula {cell_idx} [{cell['tagName']}]: {cell['text'][:80]}")
        
        # Testar extração com novo método
        print("\n" + "="*60)
        print("TESTE DE EXTRACAO")
        print("="*60)
        
        extracted = page.evaluate("""
            () => {
                let allPairs = [];
                let tables = document.querySelectorAll('table');
                
                tables.forEach(table => {
                    let rows = table.querySelectorAll('tr');
                    
                    // Procurar por linhas de CABECALHO seguidas por linhas de DADOS
                    for (let i = 0; i < rows.length - 1; i++) {
                        let headerRow = rows[i];
                        let dataRow = rows[i + 1];
                        
                        let headers = Array.from(headerRow.querySelectorAll('td, th')).map(c => c.innerText.trim());
                        let values = Array.from(dataRow.querySelectorAll('td, th')).map(c => c.innerText.trim());
                        
                        if (headers.length > 0 && headers.length === values.length) {
                            for (let j = 0; j < headers.length; j++) {
                                if (headers[j] && values[j]) {
                                    allPairs.push({
                                        label: headers[j],
                                        value: values[j]
                                    });
                                }
                            }
                        }
                    }
                    
                    // TAMBEM processar pares lado-a-lado
                    rows.forEach(row => {
                        let cells = Array.from(row.querySelectorAll('td, th'));
                        if (cells.length >= 2 && cells.length % 2 === 0) {
                            for (let i = 0; i < cells.length; i += 2) {
                                let label = cells[i].innerText.trim();
                                let value = cells[i + 1].innerText.trim();
                                if (label && value) {
                                    allPairs.push({
                                        label: label,
                                        value: value
                                    });
                                }
                            }
                        }
                    });
                });
                
                return allPairs;
            }
        """)
        
        print(f"\n[OK] Extraidos {len(extracted)} pares label-valor:")
        for pair in extracted[:20]:  # Mostrar apenas os primeiros 20
            print(f"  {pair['label']}: {pair['value']}")
        
        if len(extracted) > 20:
            print(f"  ... e mais {len(extracted) - 20} pares")
        
        # Salvar resultado completo
        with open("debug_extraction_result.json", "w", encoding="utf-8") as f:
            json.dump({
                "structure": table_structure,
                "extracted_pairs": extracted
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n[OK] Resultado completo salvo em: debug_extraction_result.json")
        print("\n[*] Pressione ENTER para fechar...")
        input()
        
        browser.close()

if __name__ == "__main__":
    debug_tables()
