"""
Debug script para verificar a estrutura do container de filhos
"""
import asyncio
from playwright.sync_api import sync_playwright

def debug_children_container():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto("https://sici.rio.rj.gov.br/PAG/principal.aspx", wait_until="networkidle")
        page.wait_for_timeout(3000)
        
        # Localizar SMS
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
        
        print(f"SMS ID: {sms_id}")
        
        # Expandir SMS
        page.evaluate(f"""
            (nodeId) => {{
                let textLink = document.getElementById(nodeId);
                if (!textLink) return false;
                
                let tr = textLink.closest('tr');
                if (!tr) return false;
                
                let allLinks = tr.querySelectorAll('a');
                for (let link of allLinks) {{
                    let img = link.querySelector('img');
                    if (img && (img.alt.includes('Expand') || img.alt.includes('Collapse'))) {{
                        link.click();
                        return true;
                    }}
                }}
                return false;
            }}
        """, sms_id)
        
        page.wait_for_load_state('networkidle', timeout=10000)
        page.wait_for_timeout(2000)
        
        # Debug: Procurar por possíveis containers
        debug_info = page.evaluate(f"""
            (smsId) => {{
                let match = smsId.match(/t(\\d+)$/);
                let nodeNum = match ? match[1] : null;
                
                let info = {{
                    smsId: smsId,
                    nodeNum: nodeNum,
                    possibleContainerIds: []
                }};
                
                if (nodeNum) {{
                    // Testar vários padrões possíveis
                    let patterns = [
                        'ContentPlaceHolder1_ua_treeviewn' + nodeNum + 'Nodes',
                        'ua_treeviewn' + nodeNum + 'Nodes',
                        'treeviewn' + nodeNum + 'Nodes',
                        't' + nodeNum + 'Nodes',
                    ];
                    
                    for (let pattern of patterns) {{
                        let el = document.getElementById(pattern);
                        info.possibleContainerIds.push({{
                            id: pattern,
                            exists: el !== null,
                            visible: el ? el.offsetParent !== null : false,
                            childrenCount: el ? el.querySelectorAll('a[id*="treeview"]').length : 0
                        }});
                    }}
                }}
                
                // Procurar por qualquer div/span com children/nodes no ID
                let allElements = document.querySelectorAll('[id*="Nodes"]');
                info.allNodesElements = [];
                for (let el of allElements) {{
                    info.allNodesElements.push({{
                        id: el.id,
                        childrenCount: el.querySelectorAll('a[id*="treeview"]').length
                    }});
                }}
                
                return info;
            }}
        """, sms_id)
        
        print("\n=== DEBUG INFO ===")
        print(f"SMS ID: {debug_info['smsId']}")
        print(f"Node Number: {debug_info['nodeNum']}")
        
        print("\nPossible Container IDs:")
        for item in debug_info['possibleContainerIds']:
            print(f"  - {item['id']}: exists={item['exists']}, visible={item['visible']}, children={item['childrenCount']}")
        
        print("\nAll Elements with 'Nodes' in ID:")
        for item in debug_info['allNodesElements']:
            print(f"  - {item['id']}: children={item['childrenCount']}")
        
        context.close()
        browser.close()

if __name__ == "__main__":
    debug_children_container()
