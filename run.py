import os
import json
import csv
import time

LANGUAGE_EXTENSIONS = ['go', 'java', 'cs', 'ex', 'rb', 'ts', 'py', 'php', 'cc', 'md', 'bazel', 'html', 'rst', 'h', 'js', 'txt', 'tmpl']
GHS_COMMAND = 'ghs code --repo=googleapis/discovery-artifact-manager --json'
REDIRECT_STDOUT = '>'
OUTPUT_FOLDER = 'data/output/'
OUTPUT_CSV_FOLDER = OUTPUT_FOLDER + 'csv'
OUTPUT_RAW_FOLDER = OUTPUT_FOLDER + 'raw/'
JSON_EXTENSION = '.json'
CSV_EXTENSION = '.csv'
INPUT_PATH = 'data/input/keywords.txt'

def is_a_file_of_language(file):
    return file.split('.')[-1] in LANGUAGE_EXTENSIONS

def is_from_api(name):
    return 'google-api' in name

def read_json(path):
    with open(path, 'r') as json_file:
        data = json.load(json_file)
    return data

def format_properly_json(json_data):
    return json.dumps(json_data, indent=4)

def write_properly_json(data, json_file):
    with open(json_file, 'w') as json_file:
        json_file.write(json.dumps(data, indent=4))

def read_and_rewrite_properly_json(path):
    write_properly_json(read_json(path), path)

def create_if_does_not_exist(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)
    return directory

def write_to_csv(keyword, rows, suffix=''):
    output_folder = create_if_does_not_exist(OUTPUT_CSV_FOLDER + suffix + '/')
    path_to_csv_output = output_folder + keyword.replace(' ', '_') + CSV_EXTENSION
    with open(path_to_csv_output, 'w', newline='\n') as csvfile:
        writer = csv.writer(csvfile, delimiter=';',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(row)

def run(keyword, all_rows, errors):

    path_to_raw_output = create_if_does_not_exist(OUTPUT_RAW_FOLDER) + keyword.replace(' ', '_') + JSON_EXTENSION
    cmd = ' '.join([
        GHS_COMMAND,
        '\"' + keyword + '\"',
        REDIRECT_STDOUT,
        path_to_raw_output
    ])
    print('run', cmd)
    os.system(cmd)
    try:
        read_and_rewrite_properly_json(path_to_raw_output)
        json_data = read_json(path_to_raw_output)
    except json.decoder.JSONDecodeError:
        errors.append(keyword)
        return all_rows

    rows_raw = []
    rows_no_languages = []
    for element in json_data:
        name = element['name']
        repository = element['repository']
        repo_name = repository['name']
        array_to_append = [keyword, name, element['html_url'], repo_name, repository['html_url']]
        rows_raw.append(array_to_append)
        if not is_a_file_of_language(name):
            all_rows.append(array_to_append)
            rows_no_languages.append(array_to_append)

    write_to_csv(keyword, rows_raw)
    write_to_csv(keyword, rows_no_languages, suffix='_no_lang')
    return all_rows

keywords_in_error = []
all_rows = []
with open(INPUT_PATH, 'r') as input_file_keywords:
    for keyword in input_file_keywords.readlines():
        if keyword.startswith('family_'):
            continue
        print('run for', keyword.strip())
        run(keyword.strip(), all_rows, keywords_in_error)
        print('waiting 10sec before another request...')
        time.sleep(10)
write_to_csv('all', all_rows, suffix='_all')
with open(OUTPUT_FOLDER + 'error.txt', 'w') as error_file:
    for keyword_in_error in keywords_in_error:
        error_file.write(keyword_in_error + '\n')
