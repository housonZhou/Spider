import json


def load_file(file_path, encoding='utf8') -> list:
    with open(file_path, 'r', encoding=encoding)as f:
        return [line.strip() for line in f if line.strip()]


def json_data(data):
    data = json.loads(data)
    text = json.loads(data.get('text'))
    text_data = text.get('data')
    for item in text_data:
        print('--' * 10)
        for k, v in item.items():
            print(k, v)
    print('==' * 20)


if __name__ == '__main__':
    json_path = r'TouTiao_news.json'
    for item in load_file(json_path):
        json_data(item)
