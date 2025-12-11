"""
Script para debugar a estrutura EXATA da tabela de informações do SMS
"""
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    print("[*] Acessando SICI...")
    page.goto("https://sici.rio.rj.gov.br/PAG/principal.aspx", timeout=60000)
    page.wait_for_timeout(2000)
    
    print("[*] Aguardando TreeView...")
    page.wait_for_selector("#ContentPlaceHolder1_ua_treeview", timeout=30000)
    
    # Encontrar e clicar no SMS
    print("[*] Procurando SMS...")
    nodes = page.query_selector_all("[id^='ContentPlaceHolder1_ua_treeviewt']")
    
    for node in nodes:
        text = node.text_content()
        if "SMS" in text and "Secretaria Municipal" in text:
            print(f"[OK] SMS encontrado, clicando...")
            node.click()
            page.wait_for_timeout(2000)
            break
    
    # Selecionar "Informações Gerais"
    print("[*] Selecionando 'Informações Gerais'...")
    selected = page.evaluate("""
        () => {
            let selects = document.querySelectorAll('select');
            for (let select of selects) {
                let options = select.querySelectorAll('option');
                for (let option of options) {
                    let text = option.innerText.trim();
                    if (text.includes('Informações Gerais') || text.includes('Informacoes Gerais')) {
                        select.value = option.value;
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                        return text;
                    }
                }
            }
            return null;
        }
    """)
    
    if selected:
        print(f"[OK] Selecionado '{selected}'")
        page.wait_for_timeout(2000)
    
    # Extrair estrutura COMPLETA das tabelas
    print("\n" + "="*80)
    print("ESTRUTURA COMPLETA DAS TABELAS")
    print("="*80)
    
    result = page.evaluate("""
        () => {
            let tableData = [];
            let tables = document.querySelectorAll('table');
            
            tables.forEach((table, tableIdx) => {
                let tableInfo = {
                    tableIndex: tableIdx,
                    rows: []
                };
                
                let rows = Array.from(table.querySelectorAll('tr'));
                
                rows.forEach((row, rowIdx) => {
                    let cells = Array.from(row.querySelectorAll('td, th'));
                    let cellsData = cells.map(cell => cell.innerText.trim());
                    
                    if (cellsData.some(c => c.length > 0)) {
                        tableInfo.rows.push({
                            rowIndex: rowIdx,
                            cellCount: cells.length,
                            cells: cellsData
                        });
                    }
                });
                
                if (tableInfo.rows.length > 0) {
                    tableData.push(tableInfo);
                }
            });
            
            return tableData;
        }
    """)
    
    # Mostrar estrutura
    for table in result:
        print(f"\n--- TABELA {table['tableIndex']} ---")
        for row in table['rows']:
            print(f"  Linha {row['rowIndex']} ({row['cellCount']} células):")
            for idx, cell in enumerate(row['cells']):
                if cell:
                    print(f"    [{idx}] = {cell[:80]}")
    
    # Salvar resultado
    with open("debug_sms_table_structure.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] Estrutura salva em: debug_sms_table_structure.json")
    print("\n[*] Pressione ENTER para fechar...")
    input()
    
    browser.close()
