"""
Ponto de entrada da aplicação RPA SICI SMS.
Executa o scraper em um contexto de gerenciamento de recursos.
"""

from .sici_scraper import SiciSmsScraper


def main():
    """
    Função principal que executa a RPA.
    Utiliza context manager para garantir limpeza de recursos.
    """
    with SiciSmsScraper() as scraper:
        scraper.run()


if __name__ == "__main__":
    main()
