"""
Scraper para extração da árvore hierárquica de órgãos da SMS no site SICI.
Utiliza Playwright (API síncrona) para automatizar o acesso e coleta de dados.

Este scraper funciona com um TreeView customizado do ASP.NET onde:
- Cada nó tem um <a> com id terminado em "i" (ex: ContentPlaceHolder1_ua_treeviewt0i)
- Os filhos de cada nó estão dentro de um <div> com id terminado em "Nodes" (ex: ContentPlaceHolder1_ua_treeviewn0Nodes)
- Os nós inicialmente colapsados têm display:none nos seus divs de filhos
"""

import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from .config import BASE_URL, HEADLESS, OUTPUT_JSON, CLICK_TIMEOUT, ROUND_TIMEOUT, COLLECTED_DATA_DIR


class SiciSmsScraper:
    """
    Classe para scraping da árvore de órgãos da SMS no site SICI.
    Automatiza a expansão de nós e extração de hierarquias.
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
        Retorna a instância da classe para uso com 'with'.
        """
        # Iniciar Playwright
        self.playwright = sync_playwright().start()
        
        # Abrir navegador Chromium
        self.browser = self.playwright.chromium.launch(headless=HEADLESS)
        
        # Criar contexto e página
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
        Cria a estrutura de diretórios para armazenar os dados coletados.
        """
        collected_path = Path(COLLECTED_DATA_DIR)
        collected_path.mkdir(parents=True, exist_ok=True)
        
        # Criar subpasta de backup/histórico
        backup_path = collected_path / "backup"
        backup_path.mkdir(parents=True, exist_ok=True)
    
    def _get_safe_filename(self, name: str) -> str:
        """
        Converte um nome em um nome de arquivo seguro.
        Remove caracteres inválidos em nomes de arquivo.
        """
        # Remover caracteres inválidos
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
        Obtém ou cria o diretório para um nó específico.
        
        Args:
            node_name: Nome do nó
            parent_path: Caminho pai (para estrutura hierárquica)
        
        Returns:
            Path: Caminho do diretório do nó
        """
        safe_name = self._get_safe_filename(node_name)
        
        if parent_path is None:
            parent_path = Path(COLLECTED_DATA_DIR)
        
        node_path = parent_path / safe_name
        node_path.mkdir(parents=True, exist_ok=True)
        
        return node_path
    
    def _save_node_data(self, node_name: str, node_data: dict, parent_path: Path = None):
        """
        Salva os dados de um nó em um arquivo JSON com nome do nó.
        
        Args:
            node_name: Nome do nó (será usado como nome do arquivo)
            node_data: Dados coletados do nó
            parent_path: Caminho pai para organização hierárquica
        """
        try:
            node_path = self._get_node_directory(node_name, parent_path)
            
            # Salvar arquivo com nome do nó e extensão .json
            safe_filename = self._get_safe_filename(node_name)
            json_file = node_path / f"{safe_filename}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(node_data, f, ensure_ascii=False, indent=2)
            
            print(f"   ✓ Dados salvos: {json_file}")
            
        except Exception as e:
            print(f"   ✗ Erro ao salvar dados de '{node_name}': {e}")

    def open_site(self):
        """
        Abre o site SICI e aguarda o carregamento da página.
        Aguarda pela árvore estar disponível (detectando um elemento da árvore).
        """
        print(f"[*] Acessando {BASE_URL}...")
        
        # Navegar para a página
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
        Expande todos os nós da árvore SMS coletando dados de cada um.
        Estratégia:
        1. Expandir SMS
        2. Clicar no nó "0" para revelar os filhos reais
        3. Acessar cada filho recursivamente
        """
        print("[*] Acessando todos os nos de SMS e coletando informacoes...")
        
        self.collected_data = {"SMS": {"info": {}, "filhos": {}}}
        
        try:
            # Encontrar e expandir SMS
            self._find_and_expand_sms()
            
            # Acessar SMS para coletar sua info
            print("├─ Acessando SMS para coletar informações...")
            sms_links = self.page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
            sms_node = None
            for link in sms_links:
                if link.text_content().strip() == "SMS":
                    sms_node = link
                    break
            
            if sms_node:
                try:
                    sms_node.click()
                    self.page.wait_for_timeout(800)
                    sms_info = self._extract_node_info()
                    self.collected_data["SMS"]["info"] = sms_info
                    print("│  └─ Informações do SMS coletadas")
                except Exception as e:
                    print(f"⚠️ Erro ao acessar SMS: {e}")
            
            # Agora encontrar o nó "0" (placeholder) e clicá-lo para revelar filhos
            print("├─ Clicando no nó '0' para revelar filhos...")
            sms_links = self.page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
            node_0 = None
            node_0_id = None
            
            for link in sms_links:
                if link.text_content().strip() == "0":
                    node_0 = link
                    node_0_id = link.get_attribute('id')
                    break
            
            if node_0:
                try:
                    # Usar JavaScript para clicar (mais confiável)
                    self.page.evaluate(f"""
                        () => {{
                            let el = document.getElementById('{node_0_id}');
                            if (el) el.click();
                        }}
                    """)
                    self.page.wait_for_load_state('networkidle')
                    self.page.wait_for_timeout(1000)
                    print("│  └─ Nó '0' clicado - filhos revelados!")
                except Exception as e:
                    print(f"⚠️ Erro ao clicar no nó '0': {e}")
                    return
            else:
                print("⚠️ Nó '0' não encontrado")
                return
            
            # Agora procurar pelos filhos reais do SMS
            print("├─ Procurando pelos filhos do SMS...")
            self.page.wait_for_timeout(2000)  # Aguardar carregamento completo
            
            # Obter todos os links
            all_links = self.page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
            print(f"│  └─ Total de links encontrados: {len(all_links)}")
            
            # Encontrar SMS e seus filhos
            sms_index = None
            filhos_sms = []
            
            for i, link in enumerate(all_links):
                if link.text_content().strip() == "SMS":
                    sms_index = i
                    break
            
            if sms_index is None:
                print("❌ SMS não encontrado na lista de links")
                return
            
            # Coletar todos os filhos diretos do SMS
            # Filhos são aqueles que vêm após SMS até encontrar outro órgão principal
            if sms_index is not None:
                for i in range(sms_index + 1, len(all_links)):
                    link = all_links[i]
                    text = link.text_content().strip()
                    link_id = link.get_attribute('id')
                    
                    # Parar se encontrar outro órgão (SMTE, SMC, etc que vêm depois de SMS)
                    # Verificar se é um órgão pelo padrão (maiúsculas, 2-4 caracteres)
                    if len(text) <= 4 and text.isupper() and text != "SMS":
                        # Encontrou próximo órgão, parar
                        break
                    
                    # Ignorar nó placeholder "0"
                    if text != "0" and text:
                        filhos_sms.append((text, link_id))
            
            if filhos_sms:
                print(f"│  └─ {len(filhos_sms)} filhos encontrados\n")
                
                # Processar cada filho
                for i, (child_text, child_id) in enumerate(filhos_sms):
                    is_last = (i == len(filhos_sms) - 1)
                    prefix = "└─" if is_last else "├─"
                    
                    print(f"{prefix} [{i+1}/{len(filhos_sms)}] Processando: {child_text}")
                    try:
                        self._expand_and_access_node(
                            child_text, 
                            self.collected_data["SMS"]["filhos"],
                            depth=1
                        )
                    except Exception as e:
                        print(f"⚠️ Erro em {child_text}: {e}")
                        self.collected_data["SMS"]["filhos"][child_text] = {"erro": str(e)}
                    
                    # Pequena pausa entre nós
                    self.page.wait_for_timeout(300)
            else:
                print("│  └─ Nenhum filho encontrado")
            
        except Exception as e:
            print(f"❌ Erro geral: {e}")

    def _find_and_expand_sms(self):
        """Helper para encontrar e expandir o nó SMS."""
        sms_links = self.page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
        sms_node = None
        sms_node_id = None
        
        for link in sms_links:
            if link.text_content().strip() == "SMS":
                sms_node = link
                sms_node_id = link.get_attribute('id')
                break
        
        if not sms_node or not sms_node_id:
            return
        
        # Extrair número do SMS
        sms_num = sms_node_id.replace('ContentPlaceHolder1_ua_treeviewt', '')
        sms_icon_id = f"ContentPlaceHolder1_ua_treeviewt{sms_num}i"
        sms_nodes_id = f"ContentPlaceHolder1_ua_treeviewn{sms_num}Nodes"
        
        sms_icon = self.page.query_selector(f"#{sms_icon_id}")
        sms_nodes_div = self.page.query_selector(f"#{sms_nodes_id}")
        
        # Expandir SMS se colapsado
        if sms_icon and sms_nodes_div:
            try:
                display = self.page.evaluate(
                    "el => window.getComputedStyle(el).display",
                    sms_nodes_div
                )
                if display == "none":
                    print("├─ Expandindo (tentativa 1): SMS")
                    sms_icon.click()
                    self.page.wait_for_timeout(800)
            except Exception as e:
                print(f"⚠️ Erro ao expandir SMS: {e}")

    def _extract_node_info(self) -> dict:
        """
        Extrai as informações estruturadas da página para o nó atualmente selecionado.
        Busca padrões de rótulo:valor nas tabelas e divs da página.
        
        Returns:
            dict: Dicionário com informações organizadas por seção
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
            
            # Extrair TÍTULO (geralmente no topo)
            try:
                title_elements = self.page.query_selector_all("h1, h2, .title, [class*='titulo'], [class*='header']")
                if title_elements:
                    title = title_elements[0].text_content().strip()
                    if title and len(title) > 3:
                        info["titulo"] = title
            except Exception:
                pass
            
            # Extrair DECRETO
            try:
                decreto_match = self.page.evaluate("""
                    () => {
                        let text = document.body.innerText;
                        let match = text.match(/Decreto[^\\n]*/i);
                        return match ? match[0] : null;
                    }
                """, timeout=3000)
                if decreto_match:
                    info["decreto"] = decreto_match
            except Exception as e:
                pass
            
            # Extrair informações de TABELAS e DIVS com pares rótulo:valor
            try:
                # Buscar todas as linhas (tr de tabelas e divs com padrão de linha)
                table_rows = self.page.query_selector_all("table tr")
                
                for row in table_rows:
                    try:
                        cells = row.query_selector_all("td, th")
                        if len(cells) < 2:
                            continue
                        
                        # Processar pares de células
                        for i in range(0, len(cells) - 1, 2):
                            try:
                                label = cells[i].text_content().strip().rstrip(":").strip()
                                value = cells[i + 1].text_content().strip()
                                
                                if not label or not value or len(label) < 2:
                                    continue
                                
                                # Categorizar informações baseado no rótulo
                                label_lower = label.lower()
                                
                                if any(x in label_lower for x in ["rua", "avenida", "av.", "endereço", "logradouro"]):
                                    info["endereco"]["logradouro"] = value
                                elif any(x in label_lower for x in ["número", "nº", "numero"]):
                                    info["endereco"]["numero"] = value
                                elif any(x in label_lower for x in ["complemento", "apto", "apartamento"]):
                                    info["endereco"]["complemento"] = value
                                elif any(x in label_lower for x in ["bairro"]):
                                    info["endereco"]["bairro"] = value
                                elif any(x in label_lower for x in ["cep", "código postal"]):
                                    info["endereco"]["cep"] = value
                                elif any(x in label_lower for x in ["cidade", "município"]):
                                    info["endereco"]["cidade"] = value
                                elif any(x in label_lower for x in ["uf", "estado"]):
                                    info["endereco"]["estado"] = value
                                elif any(x in label_lower for x in ["telefone", "fone", "celular", "whatsapp"]):
                                    info["comunicacoes"].append({
                                        "tipo": label,
                                        "valor": value
                                    })
                                elif any(x in label_lower for x in ["e-mail", "email", "correio eletrônico"]):
                                    info["comunicacoes"].append({
                                        "tipo": label,
                                        "valor": value
                                    })
                                elif any(x in label_lower for x in ["titular", "responsável", "gerente", "coordenador", "diretor"]):
                                    info["geral"]["nome"] = value
                                elif any(x in label_lower for x in ["cargo", "função", "posição"]):
                                    info["geral"]["cargo"] = value
                                else:
                                    # Adicionar como campo geral
                                    info["geral"][label] = value
                                    
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                
            except Exception as e:
                pass
            
            # Se não encontrou dados estruturados, tentar extrair do texto bruto
            if not info["geral"] and not info["endereco"] and not info["comunicacoes"]:
                try:
                    content = self.page.evaluate("() => document.body.innerText", timeout=3000)
                    lines = content.split('\n')
                    
                    # Extrair linhas relevantes
                    for line in lines[3:50]:
                        line = line.strip()
                        if ":" in line and len(line) > 5:
                            parts = line.split(":", 1)
                            if len(parts) == 2:
                                label = parts[0].strip()
                                value = parts[1].strip()
                                if label and value and len(label) > 2:
                                    info["geral"][label] = value
                except Exception:
                    pass
        
        except Exception as e:
            info["erro"] = str(e)
        
        return info

    def _expand_and_access_node(self, node_text: str, parent_dict: dict, depth: int = 0) -> int:
        """
        Expande um nó, ACESSA ele, coleta dados e processa filhos.
        
        Args:
            node_text: Texto do nó a processar
            parent_dict: Dicionário para armazenar dados do nó
            depth: Profundidade na árvore
            
        Returns:
            int: Número total de cliques realizados
        """
        # IGNORAR NÓ PLACEHOLDER "0"
        if node_text == "0":
            return 0
        
        indent = "  " * depth
        clicks = 0
        expansion_attempts = 3  # Máximo de tentativas para expandir um nó
        expansion_count = 0
        
        # PRIMEIRO: Tentar encontrar o nó (reencontra sempre para evitar detachment)
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
        
        # Extrair números e IDs
        try:
            node_num = node_id.replace('ContentPlaceHolder1_ua_treeviewt', '')
            icon_id = f"ContentPlaceHolder1_ua_treeviewt{node_num}i"
            nodes_id = f"ContentPlaceHolder1_ua_treeviewn{node_num}Nodes"
            
            # Obter ícone e container de filhos
            icon = self.page.query_selector(f"#{icon_id}")
            nodes_div = self.page.query_selector(f"#{nodes_id}")
        except Exception as e:
            print(f"{indent}⚠️ Erro ao processar IDs: {e}")
            return clicks
        
        # Se não tem ícone, é um nó folha
        if not icon or not nodes_div:
            print(f"{indent}└─ Acessando (folha): {node_text}")
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
                    
                    # Salvar dados do nó em arquivo JSON
                    self._save_node_data(node_text, node_info)
                    print(f"{indent}   └─ Informacoes coletadas")
            except Exception as e:
                parent_dict[node_text] = {"erro": str(e)}
                self._save_node_data(node_text, {"erro": str(e)})
                print(f"{indent}⚠️ Erro ao acessar folha: {e}")
            
            return clicks
        
        # Expandir o nó (tentar até expansion_attempts vezes)
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
                print(f"{indent}├─ Expandindo (tentativa {expansion_count}): {node_text}")
                try:
                    # Reencontrar ícone
                    icon = self.page.query_selector(f"#{icon_id}")
                    if icon:
                        icon.click()
                        clicks += 1
                        self.page.wait_for_timeout(600)
                except Exception as e:
                    print(f"{indent}⚠️ Erro ao expandir: {e}")
                    parent_dict[node_text] = {"erro": f"Nao foi possivel expandir: {e}"}
                    return clicks
            else:
                # Está expandido, acessar e processar filhos
                break
        
        # ACESSAR o nó
        print(f"{indent}├─ Acessando: {node_text}")
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
                
                # Salvar dados do nó em arquivo JSON
                self._save_node_data(node_text, node_info)
                print(f"{indent}   └─ Informacoes coletadas")
        except Exception as e:
            parent_dict[node_text] = {"erro": str(e), "filhos": {}}
            self._save_node_data(node_text, {"erro": str(e)})
            print(f"{indent}⚠️ Erro ao acessar: {e}")
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
        
        # Verificar se há apenas um placeholder "0" - se sim, clicar para revelar filhos reais
        if len(all_children) == 1:
            child_text = all_children[0].text_content().strip()
            if child_text == "0":
                print(f"{indent}│  └─ Encontrado placeholder '0', clicando para revelar filhos reais...")
                try:
                    all_children[0].click()
                    self.page.wait_for_load_state('networkidle')
                    self.page.wait_for_timeout(1000)
                    
                    # Tentar novamente buscar filhos após o postback
                    nodes_div = self.page.query_selector(f"#{nodes_id}")
                    if nodes_div:
                        all_children = nodes_div.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
                    else:
                        all_children = []
                except Exception as e:
                    print(f"{indent}⚠️ Erro ao clicar em placeholder '0': {e}")
                    all_children = []
        
        if all_children:
            print(f"{indent}│  └─ {len(all_children)} filhos encontrados")
            
            if "filhos" not in parent_dict[node_text]:
                parent_dict[node_text]["filhos"] = {}
            
            for i, child_link in enumerate(all_children):
                try:
                    child_text = child_link.text_content().strip()
                except Exception:
                    continue
                
                if not child_text:
                    continue
                
                # Ignorar nó placeholder "0"
                if child_text == "0":
                    continue
                
                is_last = (i == len(all_children) - 1)
                prefix = "    └─" if is_last else "    ├─"
                
                print(f"{indent}{prefix} Processando: {child_text}")
                try:
                    child_clicks = self._expand_and_access_node(
                        child_text, 
                        parent_dict[node_text]["filhos"],
                        depth + 2
                    )
                    clicks += child_clicks
                except Exception as e:
                    print(f"{indent}⚠️ Erro em filho: {e}")
                    parent_dict[node_text]["filhos"][child_text] = {"erro": str(e)}
                    continue
        
        return clicks

    def extract_sms_tree(self) -> dict:
        """
        Extrai a estrutura hierárquica APENAS dos nós DENTRO de SMS.
        
        Não pega nós de outros órgãos (PCRJ, GBP, etc).
        Apenas os que estão dentro do container de SMS.
        
        Returns:
            dict: Dicionário com a estrutura do SMS e seus filhos.
        """
        print("📊 Extraindo estrutura da árvore SMS...")

        # Encontrar o nó SMS
        all_links = self.page.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
        
        sms_id = None
        for link in all_links:
            if link.text_content().strip() == "SMS":
                sms_id = link.get_attribute('id')
                break
        
        if not sms_id:
            print("❌ SMS não encontrado!")
            return {}
        
        # Extrair número de SMS
        sms_num = sms_id.replace('ContentPlaceHolder1_ua_treeviewt', '')
        sms_nodes_id = f"ContentPlaceHolder1_ua_treeviewn{sms_num}Nodes"
        
        # Obter o container de SMS
        sms_container = self.page.query_selector(f"#{sms_nodes_id}")
        
        if not sms_container:
            print("❌ Container de SMS não encontrado!")
            return {"SMS": {}}
        
        # IMPORTANTE: Buscar APENAS links dentro do container de SMS
        # Isso garante que não pegamos nós de PCRJ, GBP, etc.
        sms_children = sms_container.query_selector_all("a[id*='ua_treeview']:not([id$='i'])")
        
        print(f"📍 Encontrados {len(sms_children)} nós dentro de SMS.")
        
        if not sms_children:
            return {"SMS": {}}
        
        # Construir hierarquia
        hierarchy = {"SMS": {}}
        stack = [(0, hierarchy["SMS"])]  # [(level, dict_ref), ...]
        
        for child_link in sms_children:
            child_text = child_link.text_content().strip()
            if not child_text:
                continue
            
            # Calcular o nível contando quantos divs "Nodes" o contêm DENTRO de SMS
            child_id = child_link.get_attribute('id')
            level = 0
            
            # Contar quantos divs Nodes de SMS contêm este link
            parent_divs = sms_container.query_selector_all("div[id$='Nodes']")
            for parent_div in parent_divs:
                try:
                    if parent_div.query_selector(f"a#{child_id}"):
                        level += 1
                except Exception:
                    pass
            
            # Ajustar pilha
            while stack and stack[-1][0] >= level:
                stack.pop()
            
            # Garantir pai
            if not stack:
                stack = [(0, hierarchy["SMS"])]
            
            # Inserir nó
            parent_dict = stack[-1][1]
            if child_text not in parent_dict:
                parent_dict[child_text] = {}
            
            stack.append((level, parent_dict[child_text]))
        
        print("✅ Estrutura de SMS extraída com sucesso.")
        return hierarchy

    def save_json(self, data: dict) -> None:
        """
        Salva a estrutura hierárquica em um arquivo JSON.
        
        Args:
            data (dict): Dicionário com a hierarquia a ser salva.
        """
        # Criar pasta 'data' se não existir
        data_dir = os.path.dirname(OUTPUT_JSON)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            print(f"📁 Pasta '{data_dir}' criada.")

        # Escrever o JSON no arquivo
        try:
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"💾 Estrutura salva em {OUTPUT_JSON}")
        except Exception as e:
            print(f"❌ Erro ao salvar JSON: {e}")

    def save_collected_data(self, data: dict) -> None:
        """
        Salva os dados coletados em um arquivo JSON estruturado.
        
        Args:
            data (dict): Dicionário com os dados coletados
        """
        # Criar pasta 'data' se não existir
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
        
        # Criar resumo (apenas estrutura de nós)
        try:
            resumo = self._criar_resumo(data)
            with open(resumo_file, "w", encoding="utf-8") as f:
                json.dump(resumo, f, ensure_ascii=False, indent=4)
            print(f"Resumo salvo em {resumo_file}")
        except Exception as e:
            print(f"Erro ao salvar resumo: {e}")

    def _criar_resumo(self, data: dict, estrutura: dict = None) -> dict:
        """
        Cria um resumo da estrutura com apenas os nomes dos nós.
        
        Args:
            data: Dados coletados
            estrutura: Dicionário para armazenar a estrutura
            
        Returns:
            dict: Estrutura resumida
        """
        if estrutura is None:
            estrutura = {}
        
        for chave, valor in data.items():
            if isinstance(valor, dict):
                if "filhos" in valor:
                    # É um nó com filhos
                    estrutura[chave] = self._criar_resumo(valor["filhos"])
                elif "info" in valor:
                    # É um nó com informações
                    estrutura[chave] = self._criar_resumo(valor.get("filhos", {}))
                else:
                    # É um nó folha ou nó sem filhos
                    estrutura[chave] = {}
            else:
                # Ignorar valores que não são dicts
                pass
        
        return estrutura

    def run(self) -> None:
        """
        Executa o fluxo completo da RPA:
        1. Abre o site SICI
        2. Expande todos os nós e acessa cada um
        3. Coleta informações de cada nó
        4. Salva os dados em arquivo JSON
        """
        print("\n" + "="*60)
        print("Iniciando RPA SICI SMS")
        print("="*60 + "\n")

        try:
            self.open_site()
            self.expand_all_nodes()
            self.save_collected_data(self.collected_data)
            
            print("\n" + "="*60)
            print("RPA concluida com sucesso!")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\nErro durante execucao: {e}\n")
            raise
