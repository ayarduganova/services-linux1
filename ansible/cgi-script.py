#!/usr/bin/env python3

import sys
import cgi
import os
from datetime import datetime
import subprocess
from pathlib import Path

class ImageHandler:
    """Обработчик загрузки и преобразования изображений"""
    
    def __init__(self):

        self.base_dir = Path("/var/www/webapp")
        self.upload_dir = self.base_dir / "original"
        self.output_dir = self.base_dir / "converted"
        self.templates_dir = self.base_dir / "html"
        
        self.upload_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        self.form_data = cgi.FieldStorage()
    
    def process_request(self):
        """Основной метод обработки запроса"""
        try:
            file_info = self._validate_and_save_file()
            if file_info.get("error"):
                return self._show_error(file_info["error"])
            
            if not self._convert_image(file_info["path"], file_info["name"]):
                return self._show_error("Не удалось преобразовать изображение")
            
            return self._show_result(file_info["name"])
            
        except Exception as e:
            return self._show_error(f"Системная ошибка: {str(e)}")
    
    def _validate_and_save_file(self):
        """Проверка и сохранение загруженного файла"""
        if "image" not in self.form_data:
            return {"error": "Файл не был загружен"}
        
        file_item = self.form_data["image"]
        if not file_item.filename:
            return {"error": "Файл не был загружен"}
        
        # Проверка типа файла
        if file_item.type not in ("image/jpeg", "image/png"):
            return {"error": "Поддерживаются только JPEG и PNG изображения"}
        
        # Генерация уникального имени
        ext = ".jpg" if file_item.type == "image/jpeg" else ".png"
        filename = f"img_{datetime.now():%Y%m%d%H%M%S}_{os.getpid()}{ext}"
        save_path = self.upload_dir / filename
        
        try:
            # Сохранение файла
            with open(save_path, "wb") as f:
                f.write(file_item.file.read())
            return {"path": save_path, "name": filename}
            
        except IOError:
            return {"error": "Ошибка записи файла"}
    
    def _convert_image(self, source_path, filename):
        """Конвертация изображения в черно-белое"""
        output_path = self.output_dir / filename
        try:
            result = subprocess.run(
                ["convert", str(source_path), "-colorspace", "Gray", str(output_path)],
                check=True,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _load_template(self, template_name, **context):
        """Загрузка HTML шаблона"""
        template_path = self.templates_dir / template_name
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
                for key, value in context.items():
                    content = content.replace(f"{{{{{key}}}}}", value)
                return content
        except IOError:
            return "<h1>Ошибка загрузки страницы</h1>"
    
    def _show_error(self, message):
        """Отображение страницы с ошибкой"""
        print("Content-Type: text/html\n")
        print(self._load_template("error.html", error_message=message))
    
    def _show_result(self, filename):
        """Отображение страницы с результатом"""
        print("Content-Type: text/html\n")
        print(self._load_template("success.html", filename=filename))

if __name__ == "__main__":
    handler = ImageHandler()
    handler.process_request()