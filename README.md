# SICI SMS RPA

RPA (Robotic Process Automation) em Python que acessa o sistema SICI da Prefeitura do Rio de Janeiro e extrai a hierarquia completa de órgãos da Secretaria Municipal de Saúde (SMS).

## O que faz

- 🌐 Acessa o site SICI: https://sici.rio.rj.gov.br/PAG/principal.aspx
- 📊 Expande automaticamente todos os nós colapsados da árvore do órgão SMS
- 🔗 Extrai a estrutura hierárquica completa de órgãos e subpastas
- 💾 Salva os dados em formato JSON estruturado

## Tecnologias

- **Python 3.8+**
- **Playwright** (API síncrona) - automação de navegador
- **Chromium** - navegador utilizado

## Como instalar

### 1. Clonar ou preparar o repositório

```bash
git clone <seu-repositorio>
cd sici-sms-rpa
```

### 2. Criar ambiente virtual (opcional, mas recomendado)

```bash
python -m venv venv

# No Windows:
venv\Scripts\activate

# No Linux/macOS:
source venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Instalar navegadores Playwright

```bash
playwright install
```

## Como executar

```bash
python -m src.main
```

A execução seguirá estes passos:

1. ✅ Abre o navegador (visível por padrão)
2. 📄 Acessa o site SICI
3. 🔍 Expande todos os nós da árvore SMS
4. 📊 Extrai a hierarquia completa
5. 💾 Salva em `data/estrutura_sms.json`

## Saída

O resultado é um arquivo JSON com a estrutura hierárquica. Exemplo:

```json
{
    "SMS": {
        "Coordenação de Atenção Básica": {
            "Clínica da Família - Unidade A": {},
            "Clínica da Família - Unidade B": {
                "Setor de Enfermagem": {},
                "Setor Administrativo": {}
            }
        },
        "Coordenação de Saúde Mental": {
            "Centro de Atenção Psicossocial": {}
        }
    }
}
```

## Configuração

As configurações principais estão em `src/config.py`:

- `HEADLESS`: Se `True`, o navegador não abre janela (roda em background)
- `CLICK_TIMEOUT`: Tempo de espera após cada clique (em ms)
- `ROUND_TIMEOUT`: Tempo de espera entre rodadas de expansão (em ms)
- `OUTPUT_JSON`: Caminho do arquivo JSON de saída

## Estrutura do Projeto

```
sici-sms-rpa/
├─ src/
│  ├─ __init__.py           # Inicialização do pacote
│  ├─ config.py             # Configurações gerais
│  ├─ sici_scraper.py       # Classe principal com toda a lógica
│  └─ main.py               # Ponto de entrada
├─ data/
│  └─ estrutura_sms.json    # Saída gerada automaticamente
├─ requirements.txt         # Dependências do projeto
├─ .gitignore              # Arquivos ignorados pelo git
└─ README.md               # Este arquivo
```

## Notas técnicas

- O script utiliza a API **síncrona** do Playwright (não é assíncrono)
- A detecção de nós para expandir se baseia em ícones `<img src*='plus'>`
- A indentação na hierarquia é calculada contando imagens "spacer"
- Todos os cliques têm tratamento de erro para evitar interrupções
- A aplicação aguarda adequadamente entre ações para o ASP.NET atualizar o DOM

## Possíveis ajustes

Dependendo de mudanças no HTML do SICI, pode ser necessário ajustar:

- Seletores CSS em `sici_scraper.py` (procure por comentários "NOTA")
- Timeouts em `config.py` se o site ficar mais lento/rápido
- Lógica de extração de nomes se a estrutura HTML mudar

## Troubleshooting

### Erro: "Árvore não encontrada"

A página pode estar carregando lentamente. Ajuste os timeouts em `config.py` ou verifique se o seletor está correto.

### Erro: "Playwright não encontrado"

Execute: `playwright install`

### JSON vazio ou incompleto

Verifique se o site estava responsivo durante a execução. Tente novamente.

## Autor

RPA desenvolvida para automação de coleta de dados do SICI.

## Licença

Consulte o arquivo LICENSE se aplicável.
