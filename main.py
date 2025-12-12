import requests
import json


class CatImageUploader:
    def __init__(self):
        self.cataas_url = "https://cataas.com/cat/says"
        self.yandex_url = "https://cloud-api.yandex.net/v1/disk"

    def clean_filename(self, text):
        """Очищает текст для использования в имени файла"""
        # Убираем лишние пробелы
        text = ' '.join(text.strip().split())
        # Заменяем недопустимые символы
        for char in [' ', '/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            text = text.replace(char, '_')
        # Ограничиваем длину
        if len(text) > 50:
            text = text[:50]
        return text

    def create_folder(self, token, folder_name):
        """Создает папку на Яндекс.Диске"""
        headers = {'Authorization': f'OAuth {token}'}
        params = {'path': folder_name}

        response = requests.put(
            f'{self.yandex_url}/resources',
            headers=headers,
            params=params
        )

        # 409 - папка уже существует, это нормально
        if response.status_code in [201, 409]:
            print(f"Папка '{folder_name}' готова")
            return True
        else:
            print(f"Не удалось создать папку: {response.status_code}")
            return False

    def upload_file(self, token, file_data, remote_path, content_type='image/jpeg'):
        """Загружает файл на Яндекс.Диск"""
        headers = {'Authorization': f'OAuth {token}'}

        # Получаем ссылку для загрузки
        params = {'path': remote_path, 'overwrite': 'true'}
        response = requests.get(
            f'{self.yandex_url}/resources/upload',
            headers=headers,
            params=params
        )

        if response.status_code != 200:
            print(f"Ошибка получения ссылки: {response.status_code}")
            return False

        upload_url = response.json()['href']

        # Загружаем файл
        upload_response = requests.put(
            upload_url,
            data=file_data,
            headers={'Content-Type': content_type}
        )

        if upload_response.status_code == 201:
            print(f"Файл загружен: {remote_path}")
            return True
        else:
            print(f"Ошибка загрузки файла: {upload_response.status_code}")
            return False

    def process(self, text, token, folder):
        """Основной метод обработки и загрузки"""
        print(f"Обрабатываем текст: '{text}'")

        # Получаем картинку с котиком
        try:
            response = requests.get(f'{self.cataas_url}/{text}', timeout=10)
            if response.status_code != 200:
                print(f"Не удалось получить картинку: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при загрузке картинки: {e}")
            return False

        # Создаем папку
        if not self.create_folder(token, folder):
            return False

        # Готовим имена файлов
        safe_text = self.clean_filename(text)
        image_filename = f"{safe_text}.jpg"
        json_filename = f"{safe_text}_info.json"

        # Загружаем картинку
        if not self.upload_file(token, response.content, f"{folder}/{image_filename}"):
            return False

        # Создаем JSON с информацией
        info = {
            'text': text,
            'filename': image_filename,
            'size_bytes': len(response.content),
            'source': 'cataas.com'
        }

        json_data = json.dumps(info, ensure_ascii=False, indent=2).encode('utf-8')

        # Загружаем JSON
        if not self.upload_file(token, json_data, f"{folder}/{json_filename}", 'application/json'):
            print("Информационный файл не загружен, но картинка сохранена")

        print("\nГотово!")
        print(f"Папка: {folder}/")
        print(f"Картинка: {folder}/{image_filename}")
        print(f"Информация: {folder}/{json_filename}")

        return True


def main():
    """Точка входа в программу"""
    print("Загрузка картинок котиков на Яндекс.Диск")
    print("=" * 40)

    uploader = CatImageUploader()

    # Запрашиваем данные
    text = input("\nВведите текст для котика: ").strip()
    if not text:
        print("Текст не может быть пустым")
        return

    folder = input("Введите название папки на Яндекс.Диске: ").strip()
    if not folder:
        print("Название папки не может быть пустым")
        return

    token = input("Введите токен Яндекс.Диска: ").strip()
    if not token:
        print("Токен не может быть пустым")
        return

    # Запускаем загрузку
    success = uploader.process(text, token, folder)

    if success:
        print("\nПрограмма завершена успешно")
    else:
        print("\nПрограмма завершилась с ошибками")


if __name__ == "__main__":
    main()