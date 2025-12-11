"""
Scraper para extracao da arvore hierarquica de orgaos da SMS no site SICI.
Utiliza Playwright (API sincrona) para automatizar o acesso e coleta de dados.

Este scraper funciona com um TreeView customizado do ASP.NET onde:
- Cada no tem um <a> com id terminado em "i" (ex: ContentPlaceHolder1_ua_treeviewt0i)
- Os filhos de cada no estao dentro de um <div> com id terminado em "Nodes" (ex: ContentPlaceHolder1_ua_treeviewn0Nodes)
- Os nos inicialmente colapsados tem display:none nos seus divs de filhos
"""

import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from .config import BASE_URL, HEADLESS, OUTPUT_JSON, CLICK_TIMEOUT, ROUND_TIMEOUT, COLLECTED_DATA_DIR


class SiciSmsScraper:
    """
    Classe para scraping da arvore de orgaos da SMS no site SICI.
    Automatiza a expansao de nos e extracao de hierarquias.
    """

    def __init__(self):
        """Inicializa os atributos da classe."""
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.collected_data = {}
        self._setup_directories()

    def __enter__(self):
        """
        Context manager: inicia o Playwright e abre o navegador.
        Retorna a instancia da classe para uso com 'with'.
        """
        # Iniciar Playwright
        self.playwright = sync_playwright().start()
        
        # Abrir navegador Chromium
        self.browser = self.playwright.chromium.launch(headless=HEADLESS)
        
        # Criar contexto e pagina
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager: fecha o navegador e encerra o Playwright.
        """
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def _setup_directories(self):
        """
        Cria a estrutura de diretorios para armazenar os dados coletados.
        """
        collected_path = Path(COLLECTED_DATA_DIR)
        collected_path.mkdir(parents=True, exist_ok=True)
        
        # Criar subpasta de backup/historico
        backup_path = collected_path / "backup"
        backup_path.mkdir(parents=True, exist_ok=True)
    
    def _get_safe_filename(self, name: str) -> str:
        """
        Converte um nome em um nome de arquivo seguro.
        Remove caracteres invalidos em nomes de arquivo.
        """
        # Remover caracteres invalidos
        invalid_chars = r'<>:"/\|?*'
        safe_name = name
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Limitar o tamanho
        max_length = 200
        if len(safe_name) > max_length:
            safe_name = safe_name[:max_length]
        
        return safe_name.strip()
    
    def _get_node_directory(self, node_name: str, parent_path: Path = None) -> Path:
        """
        Obtem ou cria o diretorio para um no especifico.
        
        Args:
            node_name: Nome do no
            parent_path: Caminho pai (para estrutura hierarquica)
        
        Returns:
            Path: Caminho do diretorio do no
        """
        safe_name = self._get_safe_filename(node_name)
        
        if parent_path is None:
            parent_path = Path(COLLECTED_DATA_DIR)
        
        node_path = parent_path / safe_name
        node_path.mkdir(parents=True, exist_ok=True)
        
        return node_path
    
    def _save_node_data(self, node_name: str, node_data: dict, parent_path: Path = None):
        """
        Salva os dados de um no em um arquivo JSON com nome do no.
        
        Args:
            node_name: Nome do no (sera usado como nome do arquivo)
            node_data: Dados coletados do no
            parent_path: Caminho pai para organizacao hierarquica
        """
        try:
            node_path = self._get_node_directory(node_name, parent_path)
            
            # Salvar arquivo com nome do no e extensao .json
            safe_filename = self._get_safe_filename(node_name)
            json_file = node_path / f"{safe_filename}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(node_data, f, ensure_ascii=False, indent=2)
            
            print(f"   [OK] Dados salvos: {safe_filename}.json")
            
        except Exception as e:
            print(f"   [ERRO] Erro ao salvar dados de '{node_name}': {e}")

    def open_site(self):
        """
        Abre o site SICI e aguarda o carregamento da pagina.
        Aguarda pela arvore estar disponivel (detectando um elemento da arvore).
        """
        print(f"[*] Acessando {BASE_URL}...")
        
        # Navegar para a pagina
        self.page.goto(BASE_URL, wait_until="networkidle")
        
        # Aguardar extra para JavaScript carregar completamente
        self.page.wait_for_timeout(2000)
        
        # Aguardar pelo TreeView customizado do SICI (componente ua_treeview)
        try:
            self.page.wait_for_selector("div[id*='ua_treeview']", timeout=10000)
            print("[OK] Pagina carregada com sucesso.")
        except Exception:
            print("[!] TreeView nao encontrado no tempo esperado, mas prosseguindo...")

    def expand_all_nodes(self):
        """
        Expande o SMS e processa todos os seus filhos recursivamente.
        """
        print("[*] Acessando todos os nos de SMS e coletando informacoes...")
        
        # Encontrar SMS
        print("[*] Localizando SMS...")
        sms_node_id = self.page.evaluate("""
            () => {
                let links = document.querySelectorAll('a[id*="ua_treeview"]');
                for (let link of links) {
                    if (link.innerText.trim() === 'SMS') {
                        return link.id;
                    }
                }
                return null;
            }
        """)
        
        if not sms_node_id:
            print("[!] No SMS nao encontrado!")
            return
        
        # Clicar no ÍCONE de expansão de SMS (não no texto)
        # O TreeView ASP.NET tem dois links: um para expandir (com imagem) e outro para selecionar (com texto)
        print("[*] Clicando no ícone de expansão de SMS...")
        
        # Primeiro, encontrar o link
        expand_link_info = self.page.evaluate(f"""
            (nodeId) => {{
                // O ícone de expansão está em um <a> com <img> no mesmo <tr>
                let textLink = document.getElementById(nodeId);
                if (!textLink) return false;
                
                let tr = textLink.closest('tr');
                if (!tr) return false;
                
                // Procurar por <a> que contém <img> com "Expand"
                let allLinks = tr.querySelectorAll('a');
                for (let link of allLinks) {{
                    let img = link.querySelector('img');
                    if (img && (img.alt.includes('Expand') || img.alt.includes('Collapse'))) {{
                        return true;
                    }}
                }}
                return false;
            }}
        """, sms_node_id)
        
        if not expand_link_info:
            print("[!] Ícone de expansão de SMS não encontrado")
            return
        
        # Sem ID, vamos usar um seletor que encontre o link direto
        # O link de expansão está dentro de uma <tr> que contém o link com texto (sms_node_id)
        # e tem uma imagem com alt contendo "Expand" ou "Collapse"
        
        expand_link_selector = f"#{sms_node_id}"
        expand_link_element = self.page.query_selector(expand_link_selector)
        
        if not expand_link_element:
            print("[!] SMS node not found")
            return
        
        # Encontrar a TR pai
        tr_element = self.page.evaluate(f"""
            (selector) => {{
                let el = document.querySelector(selector);
                if (!el) return null;
                let tr = el.closest('tr');
                return tr;
            }}
        """, expand_link_selector)
        
        if not tr_element:
            print("[!] TR parent not found")
            return
        
        # Agora clicar no link que contém a imagem de expansão
        # Vou clicar diretamente via coordenadas do elemento da imagem
        try:
            # Encontrar a imagem de expansão e clicar nela
            expand_img = self.page.query_selector(f"#{sms_node_id} ~ img, {expand_link_selector} ~ * img")
            if not expand_img:
                # Tentar outra abordagem: encontrar qualquer <a> na TR que tenha imagem
                expand_link = self.page.query_selector(f"tr:has(#{sms_node_id}) a:has(img)")
                if expand_link:
                    expand_link.click(timeout=5000)
                    expand_clicked = True
                else:
                    expand_clicked = False
            else:
                expand_img.click(timeout=5000)
                expand_clicked = True
        except Exception as e:
            print(f"[!] Falha ao clicar: {e}")
            expand_clicked = False
        
        if not expand_clicked:
            print("[!] Ícone de expansão de SMS não encontrado")
            return
        
        # Aguardar pelo postback do servidor
        try:
            self.page.wait_for_load_state('networkidle', timeout=10000)
        except:
            self.page.wait_for_timeout(ROUND_TIMEOUT + 1000)
        
        # Agora clicar no TEXTO do SMS para carregar seus dados no painel lateral
        print("[*] Clicando no texto de SMS para carregar dados...")
        self.page.evaluate(f"""
            (smsId) => {{
                let el = document.getElementById(smsId);
                if (el) el.click();
            }}
        """, sms_node_id)
        
        self.page.wait_for_timeout(ROUND_TIMEOUT)
        
        # Aguardar um pouco mais antes de processar filhos
        # Isso é crítico para o ASP.NET postback completar
        self.page.wait_for_timeout(2000)
        
        # IMPORTANTE: Processar filhos ANTES de extrair informações
        # porque _extract_node_info() pode mudar o DOM (via eventos em dropdowns)
        print("   [*] Procurando filhos do SMS...")
        self._process_children_recursive("SMS", depth=0, skip_click=True, parent_element=sms_node_id)
        
        # DEPOIS extrair informacoes do SMS
        print("[*] Extraindo informacoes do SMS...")
        sms_info = self._extract_node_info()
        self._save_node_data("SMS", sms_info)
        print("   [OK] Informacoes do SMS coletadas\n")
    
    
    def _process_children_recursive(self, parent_node_name: str, depth: int = 0, skip_click: bool = False, parent_element: str = None):
        """
        Processa recursivamente todos os filhos de um no.
        
        Args:
            parent_node_name: Nome do no pai cujos filhos serao processados
            depth: Profundidade atual na arvore
            skip_click: Se True, não clica no node (já foi clicado antes)
            parent_element: ID do elemento pai (se None, busca pelo nome)
        """
        indent = "  " * depth
        
        # Encontrar o elemento do no pai
        if parent_element is None:
            parent_element = self.page.evaluate(f"""
                (parentName) => {{
                    let allLinks = document.querySelectorAll('a[id*="ua_treeview"]');
                    for (let link of allLinks) {{
                        if (link.innerText.trim() === parentName) {{
                            return link.id;
                        }}
                    }}
                    return null;
                }}
            """, parent_node_name)
        
        if not parent_element:
            print(f"{indent}[!] No pai '{parent_node_name}' nao encontrado")
            return
        
        # Clicar no nó pai APENAS se não foi clicado antes
        if not skip_click:
            # O TreeView ASP.NET tem dois links:
            # 1. Link com imagem (ícone +/-) para EXPANDIR/COLAPSAR filhos
            # 2. Link com texto para SELECIONAR o nó
            # Precisamos clicar no link com a imagem para carregar os filhos do servidor
            
            print(f"{indent}[*] Clicando no ícone de expansão de '{parent_node_name}'...")
            
            # Encontrar e clicar no ícone de expansão
            expand_clicked = self.page.evaluate(f"""
                (nodeId) => {{
                    // Procurar pelo <a> que contém <img> com "expand"
                    // Este link está no mesmo <tr> que o link do texto
                    let textLink = document.getElementById(nodeId);
                    if (!textLink) return false;
                    
                    // Procurar na estrutura: TR > TD > A > IMG
                    let tr = textLink.closest('tr');
                    if (!tr) return false;
                    
                    // Procurar por um <a> que tem <img> com "expand"
                    let expandLinks = tr.querySelectorAll('a');
                    for (let link of expandLinks) {{
                        let img = link.querySelector('img');
                        if (img && (img.alt.includes('Expand') || img.alt.includes('Collapse') || img.src.includes('plus') || img.src.includes('minus'))) {{
                            link.click();
                            return true;
                        }}
                    }}
                    
                    return false;
                }}
            """, parent_element)
            
            if expand_clicked:
                # Aguardar o postback do servidor
                try:
                    self.page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    self.page.wait_for_timeout(ROUND_TIMEOUT + 1000)
            else:
                print(f"{indent}[!] Ícone de expansão não encontrado para '{parent_node_name}'")
        else:
            # Se skip_click=True, ainda precisa aguardar um pouco para o DOM estar pronto
            # Especialmente importante na primeira chamada quando SMS foi expandido
            # Usar wait_for_load_state como no caso acima
            try:
                self.page.wait_for_load_state('networkidle', timeout=10000)
            except:
                self.page.wait_for_timeout(ROUND_TIMEOUT + 1000)
            # Aguardar extra para garantir que o JavaScript renderizou tudo
            self.page.wait_for_timeout(3000)  # Aumentado para 3s
            
            # Também aguardar que o container de filhos fique visível
            # Este é um passo CRÍTICO quando skip_click=True
            try:
                container_id = self.page.evaluate(f"""
                    (parentId) => {{
                        let match = parentId.match(/t(\\d+)i?$/);
                        if (!match) return null;
                        return 'ContentPlaceHolder1_ua_treeviewn' + match[1] + 'Nodes';
                    }}
                """, parent_element)
                
                if container_id:
                    # Tentar esperar o container ficar visível
                    try:
                        self.page.wait_for_selector(f"#{container_id}", timeout=5000, state='attached')
                    except:
                        pass
            except:
                pass
        
        # Buscar filhos diretos usando JavaScript
        children = self.page.evaluate(f"""
            (parentId) => {{
                // Converter parentId para container ID
                // Exemplo: parentId = ContentPlaceHolder1_ua_treeviewt0i ou ContentPlaceHolder1_ua_treeviewt31
                //          container = ContentPlaceHolder1_ua_treeviewn0Nodes ou ContentPlaceHolder1_ua_treeviewn31Nodes
                let match = parentId.match(/t(\\d+)i?$/);
                if (!match) return [];
                
                let nodeIndex = match[1];
                let containerId = 'ContentPlaceHolder1_ua_treeviewn' + nodeIndex + 'Nodes';
                let childrenContainer = document.getElementById(containerId);
                
                if (!childrenContainer) {{
                    return [];
                }}
                
                // Coletar links filhos do container, deduplicando por ID
                let children = [];
                let seenIds = new Set();
                let childLinks = childrenContainer.querySelectorAll('a[id*="treeview"]');
                
                for (let link of childLinks) {{
                    let linkId = link.id;
                    
                    // Pular se já vimos esse ID
                    if (seenIds.has(linkId)) continue;
                    seenIds.add(linkId);
                    
                    let text = link.innerText.trim();
                    if (text && text !== '0') {{  // Ignorar placeholder "0"
                        children.push({{
                            id: linkId,
                            text: text
                        }});
                    }}
                }}
                
                return children;
            }}
        """, parent_element)
        
        if not children or len(children) == 0:
            print(f"{indent}[DEBUG] Nenhum filho encontrado. parent_element={parent_element}")
            print(f"{indent}[*] No '{parent_node_name}' nao tem filhos")
            return
        
        print(f"{indent}[*] Processando {len(children)} filho(s) de '{parent_node_name}':")
        
        for idx, child in enumerate(children, 1):
            child_name = child['text']
            child_id = child['id']
            
            print(f"{indent}[{idx}/{len(children)}] {child_name}")
            
            try:
                # Clicar no filho
                self.page.evaluate(f"""
                    (childId) => {{
                        let el = document.getElementById(childId);
                        if (el) el.click();
                    }}
                """, child_id)
                
                self.page.wait_for_timeout(ROUND_TIMEOUT)
                
                # Extrair informacoes
                child_info = self._extract_node_info()
                
                # Salvar dados
                self._save_node_data(child_name, child_info)
                
                # Verificar se este filho tem filhos - procurando pelo ícone de expandir
                has_children = self.page.evaluate(f"""
                    (childId) => {{
                        // Buscar o link do texto na árvore
                        let textLink = document.getElementById(childId);
                        if (!textLink) return false;
                        
                        // Procurar na mesma TR pelo ícone de expandir
                        let tr = textLink.closest('tr');
                        if (!tr) return false;
                        
                        // Buscar um <a> que tem <img> com alt contendo "Expand" ou "Collapse"
                        let expandLinks = tr.querySelectorAll('a');
                        for (let link of expandLinks) {{
                            let img = link.querySelector('img');
                            if (img && (img.alt.includes('Expand') || img.alt.includes('Collapse'))) {{
                                return true;  // Tem ícone de expandir
                            }}
                        }}
                        return false;
                    }}
                """, child_id)
                
                if has_children:
                    print(f"{indent}   [*] Expandindo '{child_name}' para ver filhos...")
                    # Expandir o filho usando o mesmo método que funcionou para SMS
                    self.page.evaluate(f"""
                        (childId) => {{
                            let textLink = document.getElementById(childId);
                            if (!textLink) return;
                            
                            let tr = textLink.closest('tr');
                            if (!tr) return;
                            
                            // Buscar o link de expandir (primeiro <a> com <img>)
                            let expandLinks = tr.querySelectorAll('a');
                            for (let link of expandLinks) {{
                                let img = link.querySelector('img');
                                if (img && (img.alt.includes('Expand') || img.alt.includes('Collapse'))) {{
                                    link.click();
                                    return;
                                }}
                            }}
                        }}
                    """, child_id)
                    
                    # Aguardar o postback do servidor
                    try:
                        self.page.wait_for_load_state('networkidle', timeout=10000)
                    except:
                        self.page.wait_for_timeout(ROUND_TIMEOUT + 1000)
                    
                    # Processar filhos deste filho recursivamente, passando o ID
                    self._process_children_recursive(child_name, depth + 1, skip_click=True, parent_element=child_id)
                
            except Exception as e:
                print(f"{indent}   [ERRO] Falha ao processar '{child_name}': {e}")
                continue
    
    def _process_node_recursive(self, node_name: str, parent_dict: dict, depth: int = 0):
        """
        Processa um no recursivamente:
        1. Expande o no (se tiver icone de +)
        2. Clica no placeholder '0' se existir para revelar filhos
        3. Coleta informacoes de cada filho
        4. Para cada filho, chama recursivamente esta funcao
        
        Args:
            node_name: Nome do no a processar
            parent_dict: Dicionario onde armazenar os filhos
            depth: Profundidade atual na arvore
        """
        indent = "  " * depth
        
        # Encontrar o no atual
        all_links = self.page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
        current_node = None
        current_node_id = None
        
        for link in all_links:
            if link.text_content().strip() == node_name:
                current_node = link
                current_node_id = link.get_attribute('id')
                break
        
        if not current_node:
            print(f"{indent}[AVISO] No '{node_name}' nao encontrado")
            return
        
        # Tentar expandir o no (verificar se tem icone de +)
        try:
            # Procurar pelo icone de expandir
            node_id_base = current_node_id.replace('t', '').replace('i', '')  # Pegar ID base
            expand_icon = self.page.query_selector(f"img[id*='{node_id_base}'][src*='plus']")
            
            if expand_icon:
                print(f"{indent}[*] Expandindo '{node_name}'...")
                expand_icon.click()
                self.page.wait_for_timeout(800)
        except:
            pass  # No nao tem filhos ou ja esta expandido
        
        # Clicar no no '0' se existir (placeholder para revelar filhos reais)
        self.page.wait_for_timeout(500)
        placeholder_found = False
        
        # Procurar pelo '0' que seria filho deste no
        all_links_after_expand = self.page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
        
        for link in all_links_after_expand:
            text = link.text_content().strip()
            if text == "0":
                link_id = link.get_attribute('id')
                # Verificar se este '0' eh filho do no atual (ID do '0' contem ID do pai)
                try:
                    print(f"{indent}   Clicando em placeholder '0'...")
                    self.page.evaluate(f"""
                        () => {{
                            let el = document.getElementById('{link_id}');
                            if (el) el.click();
                        }}
                    """)
                    self.page.wait_for_timeout(1200)
                    placeholder_found = True
                    break
                except:
                    pass
        
        # Atualizar lista de links apos clicar no '0'
        self.page.wait_for_timeout(500)
        all_links = self.page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
        
        print(f"{indent}[DEBUG] Total de links apos expansao: {len(all_links)}")
        
        # Encontrar o indice do no atual
        current_index = None
        for i, link in enumerate(all_links):
            if link.text_content().strip() == node_name:
                current_index = i
                break
        
        if current_index is None:
            print(f"{indent}[AVISO] No '{node_name}' nao encontrado apos expansao")
            return
        
        print(f"{indent}[DEBUG] No '{node_name}' esta no indice {current_index}")
        
        # Coletar filhos diretos deste no
        filhos = []
        
        # Coletar TODOS os textos de links visiveis
        all_texts = []
        for link in all_links:
            text = link.text_content().strip()
            all_texts.append(text)
        
        # Encontrar quantas vezes o no atual aparece (para saber qual pegar)
        node_count = all_texts.count(node_name)
        
        # Se eh no unico com esse nome, procurar filhos apos ele
        if node_count == 1 or depth == 0:  # Se eh SMS ou no unico
            # Procurar filhos apos o no atual
            found_current = False
            for i in range(len(all_texts)):
                if all_texts[i] == node_name and not found_current:
                    found_current = True
                    continue
                
                if found_current:
                    text = all_texts[i]
                    
                    # Ignorar '0'
                    if text == "0":
                        continue
                    
                    # Se eh depth 0 (SMS), parar ao encontrar outro orgao
                    if depth == 0:
                        if len(text) <= 5 and text.isupper() and text != node_name:
                            break  # Proximo orgao encontrado
                    
                    # Adicionar como filho
                    if text and text not in filhos:
                        filhos.append(text)
                    
                    # Limitar filhos para evitar pegar toda arvore
                    if len(filhos) >= 30:
                        break
        
        # Processar cada filho
        if filhos:
            print(f"{indent}[OK] '{node_name}' tem {len(filhos)} filho(s)\n")
            
            for i, child_name in enumerate(filhos):
                print(f"{indent}[*] [{i+1}/{len(filhos)}] Processando: {child_name}")
                
                try:
                    # Clicar no filho
                    child_clicked = False
                    all_links_updated = self.page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
                    
                    for link in all_links_updated:
                        if link.text_content().strip() == child_name:
                            link.click()
                            self.page.wait_for_timeout(800)
                            child_clicked = True
                            break
                    
                    if not child_clicked:
                        print(f"{indent}   [AVISO] Nao foi possivel clicar em '{child_name}'")
                        continue
                    
                    # Extrair informacoes do filho
                    child_info = self._extract_node_info()
                    parent_dict[child_name] = {"info": child_info, "filhos": {}}
                    
                    # Salvar dados do filho
                    self._save_node_data(child_name, child_info)
                    print(f"{indent}   [OK] Informacoes coletadas")
                    
                    # Processar recursivamente os filhos deste filho
                    self._process_node_recursive(child_name, parent_dict[child_name]["filhos"], depth + 1)
                    
                except Exception as e:
                    print(f"{indent}   [ERRO] Erro ao processar '{child_name}': {e}")
                    parent_dict[child_name] = {"erro": str(e)}
                
                self.page.wait_for_timeout(300)
        else:
            print(f"{indent}[OK] '{node_name}' nao tem filhos (no folha)\n")

    def _find_and_expand_sms(self):
        """Helper para encontrar e expandir o no SMS."""
        sms_links = self.page.query_selector_all("a[id*='ua_treeview']")
        sms_node = None
        sms_node_id = None
        
        for link in sms_links:
            if link.text_content().strip() == "SMS":
                sms_node = link
                sms_node_id = link.get_attribute('id')
                break
        
        if not sms_node or not sms_node_id:
            return None
        
        # CRITICAL: O TreeView ASP.NET carrega filhos dinamicamente via postback do servidor
        # quando o usuário clica no nó pai. Precisamos clicar no SMS e aguardar a resposta.
        try:
            print("[*] Clicando em SMS para carregar filhos...")
            # Clicar usando JavaScript para evitar "element detached" 
            self.page.evaluate(f"""
                (smsId) => {{
                    let el = document.getElementById(smsId);
                    if (el) el.click();
                }}
            """, sms_node_id)
            
            # Aguardar pela requisição ao servidor e resposta
            # O TreeView faz um postback quando você clica, que atualiza a página
            self.page.wait_for_load_state('networkidle', timeout=5000)
            
            print("[*] SMS expandido - filhos carregados do servidor")
            
        except Exception as e:
            print(f"   [AVISO] Erro ao expandir SMS: {e}")
        
        return sms_node

    def _extract_node_info(self) -> dict:
        """
        Extrai as informacoes estruturadas da pagina para o no atualmente selecionado.
        FORMATO ESPERADO (tabelas com multiplas colunas):
        Titular | Cargo
        Nome    | Secretario
        
        Endereco | Numero | Complemento
        Rua X    | 455    | 7 Andar
        
        Returns:
            dict: Dicionario com informacoes organizadas por secao
        """
        info = {
            "titulo": None,
            "decreto": None,
            "geral": {},
            "endereco": {},
            "comunicacoes": [],
            "timestamp": None
        }
        
        try:
            from datetime import datetime
            info["timestamp"] = datetime.now().isoformat()
            
            # Tentar selecionar "Informacoes Gerais" no dropdown se disponivel
            try:
                print("[*] Procurando dropdown 'Informações Gerais'...")
                selected = self.page.evaluate("""
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
                    print(f"[OK] Selecionado '{selected}' no dropdown")
                    try:
                        self.page.wait_for_timeout(2000)  # Aguardar carregar conteúdo
                    except:
                        pass  # Continuar mesmo que timeout
                else:
                    print("[!] Dropdown 'Informações Gerais' não encontrado")
                    
            except Exception as e:
                print(f"[!] Erro ao selecionar dropdown: {e}")
                pass
            
            # Extrair TITULO do cabecalho da pagina
            try:
                title_match = self.page.evaluate("""
                    () => {
                        let h1 = document.querySelector('h1, h2, h3, [class*="titulo"], .header');
                        return h1 ? h1.innerText.trim() : null;
                    }
                """)
                if title_match:
                    info["titulo"] = title_match
            except:
                pass
            
            # Extrair DECRETO
            try:
                decreto_match = self.page.evaluate("""
                    () => {
                        let text = document.body.innerText;
                        let match = text.match(/Decreto[^\\n]*/i);
                        return match ? match[0] : null;
                    }
                """)
                if decreto_match:
                    info["decreto"] = decreto_match
            except:
                pass
            
            # METODO PRINCIPAL: Extrair dados da página
            # Baseado no print do usuário, as informações estão em um layout específico:
            # - Titular/Cargo/Endereço/etc NÃO estão em tabelas HTML, mas em DIVs com CSS
            # - Comunicações estão em tabelas de 2 colunas
            try:
                extracted_data = self.page.evaluate("""
                    () => {
                        let allPairs = [];
                        
                        // MÉTODO 1: Extrair de tabelas com 2 colunas (Comunicações)
                        let tables = document.querySelectorAll('table');
                        tables.forEach(table => {
                            let rows = Array.from(table.querySelectorAll('tr'));
                            rows.forEach(row => {
                                let cells = Array.from(row.querySelectorAll('td, th')).map(c => c.innerText.trim());
                                
                                if (cells.length === 2 && cells[0] && cells[1]) {
                                    let label = cells[0];
                                    let value = cells[1];
                                    
                                    if (label.length > 0 && label.length < 100 && value.length > 0 && label !== value) {
                                        allPairs.push({
                                            label: label,
                                            value: value,
                                            method: 'table'
                                        });
                                    }
                                }
                            });
                        });
                        
                        // MÉTODO 2: Extrair TODO o texto visível e procurar por padrões
                        let contentArea = document.querySelector('#ContentPlaceHolder1_cphConteudo_divConteudoUA, [id*="Conteudo"], .content, main');
                        if (!contentArea) {
                            contentArea = document.body;
                        }
                        
                        let fullText = contentArea.innerText;
                        let lines = fullText.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        
                        // Procurar por padrões conhecidos no texto
                        for (let i = 0; i < lines.length - 1; i++) {
                            let line = lines[i];
                            let nextLine = lines[i + 1];
                            
                            // Padrão 1: Titular [TAB/espaços] Cargo
                            //           Nome [TAB/espaços] Secretário
                            if (line.includes('Titular') && line.includes('Cargo')) {
                                // Linha tem labels, próxima linha tem valores
                                let labels = line.split(/\\s{2,}|\\t/).map(s => s.trim()).filter(s => s);
                                let values = nextLine.split(/\\s{2,}|\\t/).map(s => s.trim()).filter(s => s);
                                
                                if (labels.length === values.length) {
                                    for (let j = 0; j < labels.length; j++) {
                                        if (labels[j] && values[j] && labels[j] !== values[j]) {
                                            allPairs.push({
                                                label: labels[j],
                                                value: values[j],
                                                method: 'text-pattern'
                                            });
                                        }
                                    }
                                    i++; // Pular a próxima linha
                                }
                            }
                            
                            // Padrão 2: Endereço [TAB] Número [TAB] Complemento
                            //           Rua X [TAB] 455 [TAB] 7 Andar
                            else if (line.includes('Endereço') || line.includes('Endereco')) {
                                let labels = line.split(/\\s{2,}|\\t/).map(s => s.trim()).filter(s => s);
                                let values = nextLine.split(/\\s{2,}|\\t/).map(s => s.trim()).filter(s => s);
                                
                                if (labels.length === values.length) {
                                    for (let j = 0; j < labels.length; j++) {
                                        if (labels[j] && values[j] && labels[j] !== values[j]) {
                                            allPairs.push({
                                                label: labels[j],
                                                value: values[j],
                                                method: 'text-pattern'
                                            });
                                        }
                                    }
                                    i++;
                                }
                            }
                            
                            // Padrão 3: Bairro [TAB] CEP
                            //           Cidade Nova [TAB] 20211-110
                            else if (line.includes('Bairro') && line.includes('CEP')) {
                                let labels = line.split(/\\s{2,}|\\t/).map(s => s.trim()).filter(s => s);
                                let values = nextLine.split(/\\s{2,}|\\t/).map(s => s.trim()).filter(s => s);
                                
                                if (labels.length === values.length) {
                                    for (let j = 0; j < labels.length; j++) {
                                        if (labels[j] && values[j] && labels[j] !== values[j]) {
                                            allPairs.push({
                                                label: labels[j],
                                                value: values[j],
                                                method: 'text-pattern'
                                            });
                                        }
                                    }
                                    i++;
                                }
                            }
                        }
                        
                        return allPairs;
                    }
                """)
                
                # Processar todos os pares extraidos
                if extracted_data:
                    print(f"[DEBUG] Extraidos {len(extracted_data)} pares da pagina")
                    for idx, pair in enumerate(extracted_data[:15]):  # Mostrar primeiros 15
                        method = pair.get('method', 'unknown')
                        print(f"  [{idx}] ({method}) {pair.get('label', '')}: {pair.get('value', '')[:60]}")
                    
                    for pair in extracted_data:
                        label = pair.get("label", "").strip()
                        value = pair.get("value", "").strip()
                        
                        if label and value and len(label) > 0 and len(value) > 0:
                            if not self._is_already_collected(info, label, value):
                                self._categorize_info(label, value, info)
                else:
                    print("[DEBUG] Nenhum dado extraido com JavaScript")
            
            except Exception as e:
                print(f"[!] Erro ao extrair com JavaScript: {e}")
            
            # Limpar dados vazios
            if not info.get("geral"):
                info.pop("geral", None)
            if not info.get("endereco"):
                info.pop("endereco", None)
            if not info.get("comunicacoes"):
                info.pop("comunicacoes", None)
        
        except Exception as e:
            info["erro"] = str(e)
        
        return info
    
    def _parse_line_to_info(self, line: str, info: dict):
        """
        Faz parse de uma linha de texto e extrai informacoes.
        """
        if " | " in line:
            parts = line.split(" | ")
        elif ":" in line:
            parts = line.split(":", 1)
        else:
            return
        
        if len(parts) == 2:
            label = parts[0].strip()
            value = parts[1].strip()
            
            if label and value and len(label) > 1 and len(value) > 1:
                if not self._is_already_collected(info, label, value):
                    self._categorize_info(label, value, info)

    def _categorize_info(self, label: str, value: str, info: dict):
        """
        Categoriza as informacoes extraidas baseado no rotulo.
        CAMPOS ESPERADOS:
        - Titular, Cargo
        - Endereco, Numero, Complemento, Bairro, CEP
        - Comunicacoes (Telefone corporativo, E-mail corporativo)
        
        Args:
            label: Rotulo da informacao
            value: Valor da informacao
            info: Dicionario para armazenar
        """
        label_lower = label.lower().strip()
        value_clean = value.strip()
        
        # GERAL (Titular, Cargo, Responsavel)
        if any(x in label_lower for x in ["titular", "responsavel", "gerente", "coordenador", "diretor", "superintendente", "chefe", "nome"]):
            info.setdefault("geral", {})["titular"] = value_clean
        elif any(x in label_lower for x in ["cargo", "funcao", "função", "posicao", "posição", "posto"]):
            info.setdefault("geral", {})["cargo"] = value_clean
        
        # ENDERECO (Endereco/Logradouro, Numero, Complemento, Bairro, CEP)
        elif label_lower in ["endereco", "endereço", "logradouro"] or any(x in label_lower for x in ["rua", "avenida", "av.", "av ", "praca", "praça", "alameda", "travessa", "estrada"]):
            info.setdefault("endereco", {})["logradouro"] = value_clean
        elif label_lower in ["numero", "número", "n.", "no", "nº"]:
            info.setdefault("endereco", {})["numero"] = value_clean
        elif label_lower in ["complemento", "compl.", "compl"]:
            info.setdefault("endereco", {})["complemento"] = value_clean
        elif label_lower in ["bairro", "distrito"]:
            info.setdefault("endereco", {})["bairro"] = value_clean
        elif label_lower in ["cep", "código postal", "codigo postal", "postal"]:
            info.setdefault("endereco", {})["cep"] = value_clean
        elif label_lower in ["cidade", "municipio", "município", "localidade"]:
            info.setdefault("endereco", {})["cidade"] = value_clean
        elif label_lower in ["uf", "estado", "unidade federativa"]:
            info.setdefault("endereco", {})["estado"] = value_clean
        
        # COMUNICACOES (Telefone, E-mail, Fax)
        elif any(x in label_lower for x in ["telefone", "fone", "celular", "whatsapp", "tel.", "tel ", "ramal", "corporativo"]) and "mail" not in label_lower:
            info.setdefault("comunicacoes", []).append({
                "tipo": label.strip(),
                "valor": value_clean
            })
        elif any(x in label_lower for x in ["e-mail", "email", "mail", "correio"]):
            info.setdefault("comunicacoes", []).append({
                "tipo": label.strip(),
                "valor": value_clean
            })
        elif any(x in label_lower for x in ["fax", "facs"]):
            info.setdefault("comunicacoes", []).append({
                "tipo": label.strip(),
                "valor": value_clean
            })
        
        # OUTROS CAMPOS GERAIS (qualquer outra informacao relevante)
        else:
            if len(label) > 2 and len(value_clean) > 1 and value_clean not in ["", "-", "N/A", "n/a"]:
                info.setdefault("geral", {})[label.strip()] = value_clean

    def _is_already_collected(self, info: dict, label: str, value: str) -> bool:
        """
        Verifica se uma informacao ja foi coletada para evitar duplicatas.
        
        Args:
            info: Dicionario de informacoes
            label: Rotulo
            value: Valor
        
        Returns:
            bool: True se ja foi coletado
        """
        # Verificar em geral
        if "geral" in info:
            for v in info["geral"].values():
                if isinstance(v, str) and value.lower() in v.lower():
                    return True
        
        # Verificar em endereco
        if "endereco" in info:
            for v in info["endereco"].values():
                if isinstance(v, str) and value.lower() in v.lower():
                    return True
        
        # Verificar em comunicacoes
        if "comunicacoes" in info:
            for comm in info["comunicacoes"]:
                if comm.get("valor", "").lower() == value.lower():
                    return True
        
        return False


    def _expand_and_access_node(self, node_text: str, parent_dict: dict, depth: int = 0) -> int:
        """
        Expande um no, ACESSA ele, coleta dados e processa filhos.
        
        Args:
            node_text: Texto do no a processar
            parent_dict: Dicionario para armazenar dados do no
            depth: Profundidade na arvore
            
        Returns:
            int: Numero total de cliques realizados
        """
        # IGNORAR NO PLACEHOLDER "0"
        if node_text == "0":
            return 0
        
        indent = "  " * depth
        clicks = 0
        expansion_attempts = 3  # Maximo de tentativas para expandir um no
        expansion_count = 0
        
        # PRIMEIRO: Tentar encontrar o no (reencontra sempre para evitar detachment)
        all_links = self.page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
        node_link = None
        node_id = None
        
        for link in all_links:
            text = link.text_content().strip()
            if text == node_text:
                try:
                    node_link = link
                    node_id = link.get_attribute('id')
                    break
                except Exception:
                    # Link pode ter sido desanexado
                    continue
        
        if not node_link:
            return clicks
        
        # Extrair numeros e IDs
        try:
            node_num = node_id.replace('ContentPlaceHolder1_ua_treeviewt', '')
            icon_id = f"ContentPlaceHolder1_ua_treeviewt{node_num}i"
            nodes_id = f"ContentPlaceHolder1_ua_treeviewn{node_num}Nodes"
            
            # Obter icone e container de filhos
            icon = self.page.query_selector(f"#{icon_id}")
            nodes_div = self.page.query_selector(f"#{nodes_id}")
        except Exception as e:
            print(f"{indent}[AVISO] Erro ao processar IDs: {e}")
            self._save_node_data(node_text, {"erro": str(e), "tipo": "erro_ids"})
            return clicks
        
        # Se nao tem icone, eh um no folha
        if not icon or not nodes_div:
            print(f"{indent}  Acessando (folha): {node_text}")
            try:
                # Reencontrar antes de clicar
                all_links = self.page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
                node_link = None
                for link in all_links:
                    if link.text_content().strip() == node_text:
                        node_link = link
                        break
                
                if node_link:
                    node_link.click()
                    clicks += 1
                    self.page.wait_for_timeout(500)
                    node_info = self._extract_node_info()
                    parent_dict[node_text] = node_info
                    
                    # Salvar dados do no em arquivo JSON
                    self._save_node_data(node_text, node_info)
                    print(f"{indent}     Informacoes coletadas")
            except Exception as e:
                parent_dict[node_text] = {"erro": str(e)}
                self._save_node_data(node_text, {"erro": str(e)})
                print(f"{indent}[AVISO] Erro ao acessar folha: {e}")
            
            return clicks
        
        # Expandir o no (tentar ate expansion_attempts vezes)
        while expansion_count < expansion_attempts:
            try:
                display = self.page.evaluate(
                    "el => window.getComputedStyle(el).display",
                    nodes_div
                )
            except Exception:
                display = "block"
            
            if display == "none":
                # Ainda colapsado, expandir
                expansion_count += 1
                print(f"{indent}  Expandindo (tentativa {expansion_count}): {node_text}")
                try:
                    # Reencontrar icone
                    icon = self.page.query_selector(f"#{icon_id}")
                    if icon:
                        icon.click()
                        clicks += 1
                        self.page.wait_for_timeout(600)
                except Exception as e:
                    print(f"{indent}[AVISO] Erro ao expandir: {e}")
                    parent_dict[node_text] = {"erro": f"Nao foi possivel expandir: {e}"}
                    return clicks
            else:
                # Esta expandido, acessar e processar filhos
                break
        
        # ACESSAR o no
        print(f"{indent}  Acessando: {node_text}")
        try:
            # Reencontrar antes de clicar
            all_links = self.page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
            node_link = None
            for link in all_links:
                if link.text_content().strip() == node_text:
                    node_link = link
                    break
            
            if node_link:
                node_link.click()
                clicks += 1
                self.page.wait_for_timeout(500)
                node_info = self._extract_node_info()
                parent_dict[node_text] = {"info": node_info, "filhos": {}}
                
                # Salvar dados do no em arquivo JSON
                self._save_node_data(node_text, node_info)
                print(f"{indent}     Informacoes coletadas")
        except Exception as e:
            parent_dict[node_text] = {"erro": str(e), "filhos": {}}
            self._save_node_data(node_text, {"erro": str(e)})
            print(f"{indent}[AVISO] Erro ao acessar: {e}")
            return clicks
        
        # Processar filhos
        try:
            nodes_div = self.page.query_selector(f"#{nodes_id}")
            if nodes_div:
                all_children = nodes_div.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
            else:
                all_children = []
        except Exception:
            return clicks
        
        # Verificar se ha apenas um placeholder "0" - se sim, clicar para revelar filhos reais
        if len(all_children) == 1:
            child_text = all_children[0].text_content().strip()
            if child_text == "0":
                print(f"{indent}     Encontrado placeholder '0', clicando para revelar filhos reais...")
                try:
                    all_children[0].click()
                    self.page.wait_for_load_state('networkidle')
                    self.page.wait_for_timeout(1000)
                    
                    # Tentar novamente buscar filhos apos o postback
                    nodes_div = self.page.query_selector(f"#{nodes_id}")
                    if nodes_div:
                        all_children = nodes_div.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
                    else:
                        all_children = []
                except Exception as e:
                    print(f"{indent}[AVISO] Erro ao clicar em placeholder '0': {e}")
                    all_children = []
        
        if all_children:
            print(f"{indent}     {len(all_children)} filhos encontrados")
            
            if "filhos" not in parent_dict[node_text]:
                parent_dict[node_text]["filhos"] = {}
            
            for i, child_link in enumerate(all_children):
                try:
                    child_text = child_link.text_content().strip()
                except Exception:
                    continue
                
                if not child_text:
                    continue
                
                # Ignorar no placeholder "0"
                if child_text == "0":
                    continue
                
                print(f"{indent}       [{i+1}] Processando: {child_text}")
                try:
                    child_clicks = self._expand_and_access_node(
                        child_text, 
                        parent_dict[node_text]["filhos"],
                        depth + 2
                    )
                    clicks += child_clicks
                except Exception as e:
                    print(f"{indent}[AVISO] Erro em filho: {e}")
                    parent_dict[node_text]["filhos"][child_text] = {"erro": str(e)}
                    continue
        
        return clicks

    def save_collected_data(self, data: dict) -> None:
        """
        Salva os dados coletados em um arquivo JSON estruturado.
        
        Args:
            data (dict): Dicionario com os dados coletados
        """
        # Criar pasta 'data' se nao existir
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            print(f"Pasta '{data_dir}' criada.")
        
        # Caminhos dos arquivos
        json_file = os.path.join(data_dir, "sms_informacoes.json")
        resumo_file = os.path.join(data_dir, "resumo.json")
        
        # Salvar dados completos
        try:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Dados completos salvos em {json_file}")
        except Exception as e:
            print(f"Erro ao salvar JSON completo: {e}")
        
        # Criar resumo (apenas estrutura de nos)
        try:
            resumo = self._criar_resumo(data)
            with open(resumo_file, "w", encoding="utf-8") as f:
                json.dump(resumo, f, ensure_ascii=False, indent=4)
            print(f"Resumo salvo em {resumo_file}")
        except Exception as e:
            print(f"Erro ao salvar resumo: {e}")

    def _criar_resumo(self, data: dict, estrutura: dict = None) -> dict:
        """
        Cria um resumo da estrutura com apenas os nomes dos nos.
        
        Args:
            data: Dados coletados
            estrutura: Dicionario para armazenar a estrutura
            
        Returns:
            dict: Estrutura resumida
        """
        if estrutura is None:
            estrutura = {}
        
        for chave, valor in data.items():
            if isinstance(valor, dict):
                if "filhos" in valor:
                    # Eh um no com filhos
                    estrutura[chave] = self._criar_resumo(valor["filhos"])
                elif "info" in valor:
                    # Eh um no com informacoes
                    estrutura[chave] = self._criar_resumo(valor.get("filhos", {}))
                else:
                    # Eh um no folha ou no sem filhos
                    estrutura[chave] = {}
            else:
                # Ignorar valores que nao sao dicts
                pass
        
        return estrutura

    def run(self) -> None:
        """
        Executa o fluxo completo da RPA:
        1. Abre o site SICI
        2. Expande todos os nos e acessa cada um
        3. Coleta informacoes de cada no
        4. Salva os dados em arquivo JSON
        """
        print("\n" + "="*60)
        print("Iniciando RPA SICI SMS")
        print("="*60 + "\n")

        try:
            self.open_site()
            try:
                self.expand_all_nodes()
            except Exception as e:
                print(f"[AVISO] Erro durante expansao de nos: {e}")
                print("   Continuando com dados ja coletados...")
            
            self.save_collected_data(self.collected_data)
            
            print("\n" + "="*60)
            print("RPA concluida com sucesso!")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\nErro durante execucao: {e}\n")
            raise
