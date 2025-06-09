from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QGraphicsView,QHBoxLayout, QGraphicsScene, QScrollArea, QSlider, QMenu, QAction, QGraphicsAnchorLayout, QCheckBox, QGroupBox, QPushButton
import cv2
import math
import numpy as np
from PyQt5.QtCore import Qt
import os
import unicodedata
import sys
from tkinter import Tk
from tkinter import filedialog
from PyQt5.QtGui import QImage, QPixmap
import subprocess
from pathlib import Path
import os.path
import configparser
import pathlib

class ImageMerger(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.image_paths = []
        self.use_ruchnoi = False
        self.starts_cmd = False
        self.start_cmd_checked = False
        self.prev_edit_width = ""  # переменнst для хранения предыдущего значения поля
        self.prev_path_waifu = ""
        self.prev_startup_waifu_parameter = ""


        # Создание объекта конфигурации
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')  # Загрузка сохраненных настроек из файла
        
        # Переменные для хранения значений полей
        self.prev_edit_width = self.config.get('waifu', 'input_method_waifu', fallback='')
        self.prev_startup_waifu_parameter = self.config.get('waifu', 'input_waifu_startup_parameter', fallback='')
        self.prev_path_waifu = self.config.get('waifu', 'input_path_waifu', fallback='')



        # Создание вложенного горизонтального макета и добавление в него кнопок
        buttons_layout = QHBoxLayout()
        self.button_open_file_dialog = QtWidgets.QPushButton('Выбрать с удалением предыдущих', self)
        self.button_open_file_dialog.clicked.connect(self.open_file_dialog1)
        buttons_layout.addWidget(self.button_open_file_dialog)
        self.button_open_file_dialog2 = QtWidgets.QPushButton('Добавить еще изображений', self)
        self.button_open_file_dialog2.clicked.connect(self.open_file_dialog2)
        buttons_layout.addWidget(self.button_open_file_dialog2)

        # Создание элементов интерфейса
        self.label_files = QtWidgets.QLabel('Выбранные изображения:', self)
        self.list_files = QtWidgets.QListWidget(self)
        self.list_files.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)  # Разрешаем перетаскивания элементов списка
        self.list_files.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        # Создание QGraphicsView для превью изображения с возможностью масштабирования и прокрутки
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.button_merge = QtWidgets.QPushButton('Склеить изображения', self)
        self.button_merge.clicked.connect(self.merge_images)
        self.button_save = QtWidgets.QPushButton('Сохранить результат', self)
        self.button_save.clicked.connect(self.save_merged_image)


        # Создание виджета QLineEdit
        self.edit_number = QtWidgets.QLineEdit(self)
        self.edit_number.setValidator(QtGui.QIntValidator())  # Ограничение на ввод только чисел
        self.edit_number.setMaxLength(10)  # Максимальная длина вводимого числа
        self.edit_number.textChanged.connect(self.process_input_number)  # Обработка изменения текста в поле

        

        # Создание переключателя (QCheckBox)
        self.check_use_ruchnoi = QtWidgets.QCheckBox('Использовать метод ручного ввода ширины холста для изображений при склеивании', self)
        self.check_use_ruchnoi.stateChanged.connect(self.toggle_ruchnoi)



        self.button_settings = QtWidgets.QPushButton("Настройки")
        self.button_settings.clicked.connect(self.show_settings_menu)





        


        # Создание контекстного меню
        self.context_menu = QMenu(self.list_files)
        
        # Добавление действия "Удалить" в контекстное меню
        self.delete_action = QAction("Удалить выбранное", self.list_files)
        self.delete_action.triggered.connect(self.delete_image)
        self.context_menu.addAction(self.delete_action)
        self.delete_action = QAction("Удалить все", self.list_files)
        self.delete_action.triggered.connect(self.delete_all_image)
        self.context_menu.addAction(self.delete_action)

        # Подключение обработчика события открытия контекстного меню
        self.list_files.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_files.customContextMenuRequested.connect(self.show_context_menu)

        # Создание списка файлов в новом макете
        self.list_files_right = QtWidgets.QListWidget(self)
        #self.list_files_right.setFixedWidth(100)  # Фиксированная ширина списка
        self.list_files_right.setFixedHeight(100)

        # Создание делегата для self_list_files_right
        delegate = QtWidgets.QStyledItemDelegate()
        self.list_files_right.setItemDelegate(delegate)
        
        
        # Добавление надписи "drag and drop image" в self_list_files_right
        item = QtWidgets.QListWidgetItem("drag and drop image")
        self.list_files_right.addItem(item)

        # Установка стилей для элемента списка
        item.setTextAlignment(Qt.AlignCenter)
        item.setData(Qt.UserRole, "drag_and_drop")  # Устанавка дополнительных данных элемента списка для идентификации

        # Установка флагов элемента списка
        item.setFlags(Qt.NoItemFlags)  # Устанавка флагов, запрещающих кликабельность, перетаскивание и выделение элемента

        # Применяем стили CSS для выравнивания текста по центру и по вертикали
        self.list_files_right.setStyleSheet("QListWidget::item { font-size: 16px; padding-top: 79px; }")


        # Создание макета для превью склеенных изображений и списка файлов справа
        merge_layout = QtWidgets.QVBoxLayout()
        merge_layout.addWidget(self.graphics_view)
        merge_layout.addWidget(self.list_files_right)
        self.list_files_right.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)  # Разрешение перетаскивания элементов списка
        self.list_files_right.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)  # Разрешение множественного выделения элементов списка
        self.list_files_right.setAcceptDrops(True)  # Разрешение принятия элементов списка при перетаскивании

        # Добавление обработчика события перетаскивания файлов
        self.list_files_right.dragEnterEvent = self.drag_enter_event
        self.list_files_right.dropEvent = self.drop_event


        # Создание ползунков масштабирования
        self.slider_zoom_in = QSlider(Qt.Horizontal)
        self.slider_zoom_in.setMinimum(0)
        self.slider_zoom_in.setMaximum(20)
        self.slider_zoom_in.setValue(0)
        self.slider_zoom_in.setTickInterval(1)
        self.slider_zoom_in.setTickPosition(QSlider.TicksBelow)
        self.slider_zoom_in.valueChanged.connect(self.zoom_image)

        # Установка ползунка масштабирования в крайнее левое положение
        self.slider_zoom_in.setSliderPosition(0)
        
        # Создание макета интерфейса
        layout = QtWidgets.QVBoxLayout(self)

        # Создание горизонтального макета для списка файлов и окна превью
        files_layout = QtWidgets.QHBoxLayout()
        files_layout.addWidget(self.list_files)
        files_layout.addLayout(merge_layout)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.label_files)
        layout.addLayout(files_layout)
        layout.addWidget(self.button_merge)
        layout.addWidget(self.button_save)
        layout.addWidget(self.slider_zoom_in)
        layout.addWidget(self.check_use_ruchnoi)
        layout.addWidget(self.edit_number)

        
        # Добавление кнопки "Настройки" в макет
        layout.addWidget(self.button_settings)


        self.list_files.setIconSize(QtCore.QSize(80, 60))

        
        # Инициализация переменных масштабирования
        self.scale_factor = 0
        self.image = None


    
    def open_file_dialog2(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter('Image files (*.jpg *.jpeg *.png)')
        file_paths, _ = file_dialog.getOpenFileNames()
        
        for path in file_paths:
            q_image = QtGui.QImage(path)
            # Изменение размера изображения
            small_image = q_image.scaled(QtCore.QSize(80, 60), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Создание пустого QPixmap
            pixmap = QtGui.QPixmap(80, 60)
            pixmap.fill(Qt.transparent)
            
            # Рисование центрированного изображения на QPixmap
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            
            x = (80 - small_image.width()) // 2
            y = (60 - small_image.height()) // 2
            painter.drawImage(x, y, small_image)
            painter.end()
            
            # Создание иконки из QPixmap
            icon = QtGui.QIcon(pixmap)
            
            item = QtWidgets.QListWidgetItem(icon, path)
            # Добавление пути к файлу и названия файла в список файлов
            file_name = os.path.basename(path)
            item.setText(f"{file_name} - {path}")  # Отображение названия файла и статичного пути
            #item.setTextAlignment(Qt.AlignCenter)
            self.list_files.addItem(item)

    def open_file_dialog1(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter('Image files (*.jpg *.jpeg *.png)')
        file_paths, _ = file_dialog.getOpenFileNames()
        
        self.list_files.clear()
        
        for path in file_paths:
            q_image = QtGui.QImage(path)
            # Изменение размера изображения
            small_image = q_image.scaled(QtCore.QSize(80, 60), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Создание пустого QPixmap
            pixmap = QtGui.QPixmap(80, 60)
            pixmap.fill(Qt.transparent)
            
            # Рисование центрированного изображения на QPixmap
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            
            x = (80 - small_image.width()) // 2
            y = (60 - small_image.height()) // 2
            painter.drawImage(x, y, small_image)
            painter.end()
            
            # Создание иконки из QPixmap
            icon = QtGui.QIcon(pixmap)
            
            item = QtWidgets.QListWidgetItem(icon, path)
            # Добавление пути к файлу и названия файла в список файлов
            file_name = os.path.basename(path)
            item.setText(f"{file_name} - {path}")  # Отображение названия файла и статичного пути
            #item.setTextAlignment(Qt.AlignCenter)
            self.list_files.addItem(item)


    def merge_images(self):
        if self.list_files.count() != 0:
            if self.use_ruchnoi:
                self.merge_images_ruchnoi()  # Добавлен аргумент target_width
            else:
                file_paths = [self.list_files.item(i).text().split(" - ")[-1] for i in range(self.list_files.count())]
                images = []
                max_width = 0
                for path in file_paths:
                    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if image is not None:
                        height, width, channel = image.shape
                        if width > max_width:
                            max_width = width
                        images.append(image)
                for i in range(len(images)):
                    if images[i].shape[1] < max_width:
                        scale_factor = max_width / images[i].shape[1]
                        images[i] = cv2.resize(images[i], None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)
                result = cv2.vconcat(images)
                height, width, channel = result.shape
                q_image = QtGui.QImage(result.data, width, height, channel * width, QtGui.QImage.Format_BGR888)
                q_pixmap = QtGui.QPixmap.fromImage(q_image)
                self.image=result
                self.graphics_scene.clear()
                self.graphics_scene.addPixmap(q_pixmap)
                self.graphics_scene.setSceneRect(QtCore.QRectF(q_pixmap.rect()))
                self.graphics_view.fitInView(self.graphics_scene.sceneRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        else:
            QMessageBox.warning(self, "Ошибка", "Отсутствуют изображения для склейки")


    def save_merged_image(self):
        if self.image is not None:
            file_dialog = QFileDialog()
            file_dialog.setAcceptMode(QFileDialog.AcceptSave)
            file_dialog.setFileMode(QFileDialog.AnyFile)
            file_dialog.setNameFilter("Images (*.jpg *.png)")
            file_dialog.setWindowTitle("Сохранить изображение")
            if file_dialog.exec_():
                self.file_path = file_dialog.selectedFiles()[0]
                if self.file_path:
                    with open(self.file_path, 'wb') as f:
                        f.write(cv2.imencode('.png', self.image)[1].tobytes())
                    if self.starts_cmd:
                        self.waifu_cmd()
                        QMessageBox.information(self, "Сохранение", "Изображение успешно сохранено с использованием waifu.")
                    else:
                        print(self.file_path)
                        QMessageBox.information(self, "Сохранение", "Изображение успешно сохранено без использования waifu.")
        else:
            QMessageBox.warning(self, "Ошибка", "Нет изображения для сохранения.")
            
            
    def zoom_image(self, value):
        # Обновление масштабный коэффициент на основе значения ползунка
        self.scale_factor = 0.2 + value / 10
        # Сброс текущего преобразования
        self.graphics_view.resetTransform()
        # Применение нового масштабирования
        self.graphics_view.scale(self.scale_factor, self.scale_factor)



    def add_image(self, file_path):
        if file_path not in self.image_paths:
            self.image_paths.append(file_path)
            self.list_files.addItem(file_path)

    def drag_enter_event(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def drop_event(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith(".jpg") or file_path.endswith(".png"):
                q_image = QtGui.QImage(file_path)
                # Изменение размера изображения
                small_image = q_image.scaled(QtCore.QSize(80, 60), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                # Создание пустого QPixmap
                pixmap = QtGui.QPixmap(80, 60)
                pixmap.fill(Qt.transparent)
                
                # Рисование центрированного изображения на QPixmap
                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                
                x = (80 - small_image.width()) // 2
                y = (60 - small_image.height()) // 2
                painter.drawImage(x, y, small_image)
                painter.end()
                
                # Создание иконки из QPixmap
                icon = QtGui.QIcon(pixmap)
                
                item = QtWidgets.QListWidgetItem(icon, file_path)
                # Добавление пути к файлу и названия файла в список файлов
                file_name = os.path.basename(file_path)
                item.setText(f"{file_name} - {file_path}")  # Отображение названия файла и статичного пути
                #item.setTextAlignment(Qt.AlignCenter)
                self.list_files.addItem(item)
                
                event.acceptProposedAction()

    def show_context_menu(self, pos):
        # Получение позиции клика
        global_pos = self.list_files.mapToGlobal(pos)
        # Получение списка выделенных элементов
        selected_items = self.list_files.selectedItems()
        if selected_items:
            # Если есть выделенные элементы, то показываем контекстное меню
            self.context_menu.exec_(global_pos)


    def delete_image(self):
        # Получение списка выбранных элементов
        selected_items = self.list_files.selectedItems()
        # Проверка, что выбран хотя бы один элемент
        if len(selected_items) == 0:
            QMessageBox.warning(self.list_files, "Предупреждение", "Выберите элемент(ы) для удаления.", QMessageBox.Ok)
            return
        # Удаление элементов из списка файлов и списка путей
        for item in reversed(selected_items):
            row = self.list_files.row(item)
            if row >= 0 and row < self.list_files.count():
                self.list_files.takeItem(row)
                if row < len(self.image_paths):
                    del self.image_paths[row]

    def delete_all_image(self):
        selected_items = self.list_files.selectedItems()  # Получение списка выбранных элементов
        self.list_files.clear()


    def toggle_ruchnoi(self, state):
        if state == Qt.Checked:
            self.use_ruchnoi = True
        else:
            self.use_ruchnoi = False


    def merge_images_ruchnoi(self):
        # Ручной метод склеивания изображений
        target_width = self.target_width_input
        file_paths = [self.list_files.item(i).text().split(" - ")[-1] for i in range(self.list_files.count())]
        images = []
        max_width = 0
        for path in file_paths:
            image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is not None:
                height, width, channel = image.shape
                if width > max_width:
                    max_width = width
                images.append(image)
        
        for i in range(len(images)):
            if images[i].shape[1] != target_width:
                scale_factor = target_width / images[i].shape[1]
                images[i] = cv2.resize(images[i], None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)
        
        result = cv2.vconcat(images)
        height, width, channel = result.shape
        aspect_ratio = target_width / width
        new_height = int(height * aspect_ratio)
        result = cv2.resize(result, (target_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        q_image = QtGui.QImage(result.data, target_width, new_height, channel * target_width, QtGui.QImage.Format_BGR888)
        q_pixmap = QtGui.QPixmap.fromImage(q_image)
        self.image = result
        self.graphics_scene.clear()
        self.graphics_scene.addPixmap(q_pixmap)
        self.graphics_scene.setSceneRect(QtCore.QRectF(q_pixmap.rect()))
        self.graphics_view.fitInView(self.graphics_scene.sceneRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)


    def process_input_number(self):
        # Метод, вызываемый при нажатии клавиши Enter в виджете QLineEdit
        if self.edit_number.text():
            self.target_width_input = int(self.edit_number.text())  # Получение введенного числа из виджета
        print(self.target_width_input)
        print(self.starts_cmd)

    def toggle_use_cmd(self,state):
        if state == Qt.Checked:
            self.starts_cmd = True
            self.start_cmd_checked = True  # сохранение состояния переключателя
        else:
            self.starts_cmd = False
            self.start_cmd_checked = False  # сохранение состояния переключателя

    def show_settings_menu(self):
        # Создание нового диалогового окна для настроек
        settings_dialog = QtWidgets.QDialog(self)
        settings_dialog.setWindowTitle("Настройки")

        # Создание элементов интерфейса для настроек
        label_width = QtWidgets.QLabel("Параметры обработки изображений waifu:")
        label_path_waifu = QtWidgets.QLabel("Путь к waifu:")
        label_startup_waifu = QtWidgets.QLabel("Параметр запуска waifu:")
        
        #Создание виджета QLineEdit "optionals waifu"
        self.edit_width = QtWidgets.QLineEdit(self)
        self.edit_width.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[А-Яа-яA-Za-z0-9_&.;:\\\\ -/]+")))
        self.edit_width.setMaxLength(200)  # Максимальная длина вводимого числа
        self.edit_width.textChanged.connect(self.input_method_waifu)  # Обработка изменения текста в поле
        self.edit_width.setText(self.prev_edit_width)

        #Создание виджета QLineEdit "waifu startup parameter"
        self.startup_parameter_waifu = QtWidgets.QLineEdit(self)
        self.startup_parameter_waifu.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[А-Яа-яA-Za-z0-9_&.;:\\\\ -/]+")))
        self.startup_parameter_waifu.setMaxLength(100)  # Максимальная длина вводимого числа
        self.startup_parameter_waifu.textChanged.connect(self.input_waifu_startup_parameter)  # Обработка изменения текста в поле
        self.startup_parameter_waifu.setText(self.prev_startup_waifu_parameter)
        
        # Добавление возможности вставки текста при помощи комбинации клавиш ctrl+v
        self.edit_width.setContextMenuPolicy(Qt.NoContextMenu)
        self.edit_width.setPlaceholderText("Введите текст...")
        self.edit_width.setReadOnly(False)
        self.edit_width.setClearButtonEnabled(True)
        self.edit_width.addAction(
            QtWidgets.QAction("Вставить", self.edit_width, triggered=self.edit_width.paste),
            QtWidgets.QLineEdit.TrailingPosition
        )

        #Создание виджета QLineEdit "path waifu"
        self.path_waifu = QtWidgets.QLineEdit(self)
        self.path_waifu.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[А-Яа-яA-Za-z0-9_&.;:\\\\ -/]+")))
        self.path_waifu.setMaxLength(100)  # Максимальная длина вводимого числа
        self.path_waifu.textChanged.connect(self.input_path_waifu)  # Обработка изменения текста в поле
        self.path_waifu.setText(self.prev_path_waifu)

        # Создание переключателя (QCheckBox) "включение waifu"
        self.start_cmd = QtWidgets.QCheckBox('Использовать waifu', self)
        self.start_cmd.stateChanged.connect(self.toggle_use_cmd)
        self.start_cmd.setChecked(self.start_cmd_checked)
        

        # Создание кнопок "Применить" и "Отмена"
        button_apply = QtWidgets.QPushButton("Применить")
        button_apply.clicked.connect(self.save_settings)
        button_cancel = QtWidgets.QPushButton("Отмена")
        button_cancel.clicked.connect(settings_dialog.reject)

        # Создание макета для элементов интерфейса настроек
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.start_cmd)
        layout.addWidget(label_width)
        layout.addWidget(self.edit_width)
        layout.addWidget(label_path_waifu)
        layout.addWidget(self.path_waifu)
        layout.addWidget(label_startup_waifu)
        layout.addWidget(self.startup_parameter_waifu)
        layout.addWidget(button_apply)
        layout.addWidget(button_cancel)

        # Установка макета для диалогового окна
        settings_dialog.setLayout(layout)

        # Показ диалогового окна
        settings_dialog.exec_()


    #Принятие текста "path to waifu", отвечает за путь к папке waifu
    def input_path_waifu(self):
        if self.path_waifu.text():
            self.input_waifu_path = self.path_waifu.text().encode('utf-8')
            self.prev_path_waifu = self.input_waifu_path.decode('utf-8')
            self.input_waifu_path_decode = self.input_waifu_path.decode('utf-8')
        print(self.input_waifu_path_decode)
    
    #Принятие текста "optionals waifu", отвечает за параметры обработки изображений waifu
    def input_method_waifu(self):
        if self.edit_width.text():
            self.input_waifu = self.edit_width.text().encode('utf-8')
            self.prev_edit_width = self.input_waifu.decode('utf-8')
            self.input_waifu_decode = self.input_waifu.decode('utf-8')
        print(self.input_waifu_decode)

    #Принятие текста "Параметр запуска", отвечает за запуск waifu через cmd
    def input_waifu_startup_parameter(self):
        if self.startup_parameter_waifu.text():
            self.input_startup_parameter = self.startup_parameter_waifu.text().encode('utf-8')
            self.prev_startup_waifu_parameter = self.input_startup_parameter.decode('utf-8')
            self.input_waifu_startup_parameter_decode = self.input_startup_parameter.decode('utf-8')
        print(self.input_waifu_startup_parameter_decode)

    def waifu_cmd(self):
        path_to_image = Path(self.file_path)
        path_to_image = path_to_image.parent
        path_to_image_check = str(path_to_image) + '\\output\\'
        path_last_component = pathlib.PurePath(self.file_path).name
        path_last_component = path_last_component.partition('.')[0]
        #path_last_component = path_last_component.replace('.jpg', '')
        #path_last_component = path_last_component.replace('.png', '')
        #path_last_component = path_last_component.replace('.webp', '')
        b = 'jpg','png','webp'
        n = ''
        for i in b:
            #print(self.input_waifu_decode, i)
            if str(i) in self.input_waifu_decode:
                n = '.' + i
                break
            else:
                n = '.jpg'
        #print(path_to_image, path_to_image_check, n, path_last_component, self.input_waifu_decode)

        # Проверка папки
        if not os.path.exists(path_to_image_check):
            # Создание папки, если ее нет
            os.makedirs(path_to_image_check)


        
        a='A:','B:','C:','D:','E:','F:','G:','H:','I:','J:','K:','M:','N:','O:','P:','R:','S:','T:','U:','X:','Z:','V:','Q:','W:'

        for i in a:
            if str(i) in self.input_waifu_path_decode:
                cmd = r'c:\windows\system32\cmd.exe /C chdir /'+i[0]+ ' ' +str(self.input_waifu_path_decode)+ ' ' + '&' + ' ' +str(self.input_waifu_startup_parameter_decode)+ \
                ' ' + '-i' + ' '+'"'+str(Path(self.file_path))+'"'+ ' ' + '-o' + ' '+ '"' + str(path_to_image_check)+ path_last_component + n + '"' + ' ' + str(self.input_waifu_decode)
                print(cmd)
                subprocess.run(cmd)
                
    # Сохранение настройки в файл конфигурации
    def save_settings(self):
        self.config.set('waifu', 'input_method_waifu', self.edit_width.text())
        self.config.set('waifu', 'input_waifu_startup_parameter', self.startup_parameter_waifu.text())
        self.config.set('waifu', 'input_path_waifu', self.path_waifu.text())

        with open('config.ini', 'w') as config_file:
            self.config.write(config_file)


                    
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = ImageMerger()
    window.show()
    app.exec_()
