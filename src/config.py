"""
Configurações gerais da RPA SICI SMS.
"""

# URL base do site SICI
BASE_URL = "https://sici.rio.rj.gov.br/PAG/principal.aspx"

# Se True, o navegador roda sem abrir a janela (headless)
# Se False, a janela do navegador fica visível
HEADLESS = False

# Caminho do arquivo JSON de saída
OUTPUT_JSON = "data/estrutura_sms.json"

# Pasta para armazenar dados coletados de cada nó
COLLECTED_DATA_DIR = "collected_data"

# Timeout padrão (em milissegundos) entre cliques para o ASP.NET atualizar o DOM
CLICK_TIMEOUT = 700

# Timeout padrão entre rodadas de expansão de nós
ROUND_TIMEOUT = 1000

