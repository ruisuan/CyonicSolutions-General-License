import json
import os
import re
import concurrent.futures
from googletrans import Translator

def load_languages(json_file):
    """Carrega a lista de idiomas a partir de um arquivo JSON."""
    with open(json_file, 'r', encoding='utf-8') as file:
        return json.load(file)

def read_file(file_path):
    """Lê o conteúdo do arquivo."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def write_file(file_path, content):
    """Escreve o conteúdo no arquivo."""
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def replace_non_translatable(text):
    """Substitui partes não traduzíveis por marcadores únicos."""
    patterns = {
        'URL': r'https?://[^\s]+',
        'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    }
    markers = {}
    marker_count = 0

    def generate_marker(name, count):
        return f'__{name}_{count}__'

    for name, pattern in patterns.items():
        for match in re.finditer(pattern, text):
            marker = generate_marker(name, marker_count)
            markers[marker] = match.group()
            text = text.replace(match.group(), marker)
            marker_count += 1

    return text, markers

def translate_text(text, dest_language):
    """Traduz o texto para o idioma de destino usando o Google Translate."""
    translator = Translator()
    try:
        return translator.translate(text, dest=dest_language).text
    except Exception as e:
        print(f'Erro na tradução para {dest_language}: {e}')
        return None

def append_disclaimer(text):
    """Adiciona um aviso sobre a tradução automatizada e a versão oficial."""
    disclaimer = (
        "\n\n---\n"
        "Disclaimer: This translation was generated automatically and may not be completely accurate."
        " The official version of the license is the English version available on the GitHub repository: "
        "https://github.com/cyonicsolutions/license/license.md. Please refer to the original version for the valid license."
    )
    return text + disclaimer

def translate_in_batches(text, languages, batch_size, licenses_dir):
    """Traduz o texto em lotes para vários idiomas e salva em arquivos."""
    def worker(batch):
        results = {}
        for lang_code, lang_name in batch:
            try:
                translated_text = translate_text(text, lang_code)
                if translated_text:
                    translated_text_with_disclaimer = append_disclaimer(translated_text)
                    file_path = os.path.join(licenses_dir, f'{lang_code}.md')
                    write_file(file_path, translated_text_with_disclaimer)
                    results[lang_name] = file_path
                else:
                    results[lang_name] = None
            except Exception as e:
                print(f'Erro ao traduzir para {lang_name} ({lang_code}): {e}')
                results[lang_name] = None
        return results

    lang_items = list(languages.items())
    batches = [lang_items[i:i + batch_size] for i in range(0, len(lang_items), batch_size)]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(worker, batch) for batch in batches]
        for future in concurrent.futures.as_completed(futures):
            results = future.result()
            for lang_name, file_path in results.items():
                if file_path:
                    print(f'Tradução para {lang_name} concluída e salva em {file_path}')
                else:
                    print(f'Falha ao traduzir para {lang_name}')

def update_readme_table(licenses_dir, readme_path):
    """Atualiza o README.md com uma tabela de links para os arquivos traduzidos."""
    table_header = (
        "# CyonicSolutions General License Translations\n\n"
        "Search for your language below:"
        "| Language | Link |\n"
        "|----------|------|\n"
    )

    table_rows = ""
    for file_name in os.listdir(licenses_dir):
        if file_name.endswith('.md'):
            lang_code = os.path.splitext(file_name)[0]
            # Obtemos lang_name diretamente da chave do dicionário languages
            # que usamos para criar o batch. Como estamos gerando a tabela depois, a
            # correspondência é feita aqui usando um dicionário auxiliar.
            lang_name = next((name for code, name in languages.items() if code == lang_code), lang_code)
            link = f"[{lang_name} ({lang_code})](licenses/{file_name})"
            table_rows += f"| {lang_name} | {link} |\n"

    write_file(readme_path, table_header + table_rows)

def main():
    licenses_dir = 'licenses'
    readme_path = 'README.md'
    json_file = 'languages.json'

    os.makedirs(licenses_dir, exist_ok=True)

    global languages  # Necessário para usar no update_readme_table
    languages = load_languages(json_file)
    
    text = read_file('license.md')
    text_with_markers, markers = replace_non_translatable(text)
    
    translate_in_batches(text_with_markers, languages, batch_size=5, licenses_dir=licenses_dir)
    update_readme_table(licenses_dir, readme_path)

if __name__ == '__main__':
    main()
