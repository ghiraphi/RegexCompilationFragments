# -*- coding: utf-8 -*-
import os
import re
import json
from copy import deepcopy
from stand.text import obj_zamen

big_count = 3

class transform(object):

    hdbk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), u'hdbks/')
    raw_hdbk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), u'raw_hdbks/')

    @classmethod
    def walk_contraversions(cls, app='main', path=hdbk_path):
        """
        Собирает словари из нужной папки
        atr app: приоритет
        atr path: путь к папке с hdbks
        return: сбор данных с информацией о ключах, исклах и правилах
        """
        contraversions = os.listdir(path)
        made = {app: {'kluch_settings': [], 'rule_settings': []}}
        for contraversion in contraversions:
            made = cls.walk_labels(contraversion, path, made, app)
        return made

    @classmethod
    def walk_labels(cls, contraversion, path, made, app):
        """
        Обновляет данные для каждого тега в наборе тегов
        atr contraversion: имя справочника
        atr path: путь к корневому каталогу
        atr data: структура настроек
        atr app: приоритет
        return: обновленные настройки
        """
        cont_path = path + contraversion
        labels = os.listdir(cont_path)
        for label in labels:
            made = cls.walk_hdbks(label, cont_path, made, app, contraversion)
        return made

    @classmethod
    def walk_hdbks(cls, label, cont_path, made, app, contraversion):
        """
        Перебор файлов в каталоге для загрузки словарей
        atr label: имя справочника
        atr cont_path: путь к корневому каталогу
        atr data: структура настроек
        atr app: тип настроек (флаг приоритета приложения)
        atr contraversion: имя тега, который будет сохранен в данных
        return: выводит обновлённые настройки
        """
        label_put = cont_path + u'/' + label
        if u'customization' not in label and u'~' not in label:
            hdbk_files = os.listdir(label_put)
            label_set = {}
            label_set['label'] = label
            label_set['label_name'] = label
            label_set['roles'] = ['article']
            label_set['single_kluch'] = []
            label_set['composed_kluch'] = []
            label_set['single_iskl'] = []
            label_set['composed_iskl'] = []
            label_set['excluded_sources'] = []

            label_set['rasst_kluch'] = []
            label_set['rasst_iskl'] = []

            for hdbk_file in hdbk_files:
                if u'~' not in hdbk_file:
                    label_set = cls.load_from_files(hdbk_file, label_put, label_set,
                                                       'composed_iskl',
                                                       'composed_kluch', 'single_iskl',
                                                       'single_kluch', 'rasst_kluch',
                                                       'rasst_iskl')
            made[app]['kluch_settings'].append(label_set)
        elif u'~' not in label:
            label_set_prav = {}
            label_set_prav['label'] = contraversion
            label_set_prav['label_name'] = contraversion
            label_set_prav['roles'] = ['article']
            label_set_prav['single_stop'] = []
            label_set_prav['composed_stop'] = []
            label_set_prav['single_stop_iskl'] = []
            label_set_prav['composed_stop_iskl'] = []

            label_set_prav['rasst_stop'] = []
            label_set_prav['rasst_stop_iskl'] = []

            label_set_prav['single_newsbreak_stop'] = []
            label_set_prav['composed_newsbreak_stop'] = []

            hdbk_files = os.listdir(label_put)
            for hdbk_file in hdbk_files:
                if u'rules' in hdbk_file and u'~' not in hdbk_file and u'machine' not in hdbk_file:
                    rule_path = label_put + u'/' + hdbk_file
                    rules = cls.read_rules(rule_path)
                    label_set_prav['rules'] = rules
                elif u'machine' not in hdbk_file:
                    label_set_prav = cls.load_from_files(hdbk_file, label_put, label_set_prav,
                                                            'composed_stop_iskl',
                                                            'composed_stop', 'single_stop_iskl',
                                                            'single_stop', 'rasst_stop',
                                                            'rasst_stop_iskl',
                                                            'single_newsbreak_stop', 'composed_newsbreak_stop')
            made[app]['rule_settings'].append(label_set_prav)

        return made

    @classmethod
    def evolve_rasst(cls, template, current_id='unknown'):
        """
        Обновляет шаблон rasst
        atr template: шаблон
        atr current_id: номер справочника
        return: список обновленных шаблонов
        """
        parts = template[::2]
        dsts_raw = template[1::2]
        dsts = []
        dst_pos = 0
        multi_template = []
        evolved_amount = 0
        for part in parts:
            if part is None:
                if dsts and len(dsts_raw) > 1 and dst_pos < len(dsts_raw):
                    dsts[-1] += dsts_raw[dst_pos]
                dst_pos += 1
                continue
            part_variants = cls.creat_single_and_composed([part], current_id)
            if part_variants is None:
                return None
            if u'.*' not in part:
                multi_template.append([[part]])
            elif evolved_amount > big_count:
                multi_template.append([[part]])
            else:
                if u'(' in part and u')' in part:
                    evolved_amount += 1
                multi_template.append(part_variants)
            if dst_pos < len(dsts_raw):
                dsts.append(dsts_raw[dst_pos])
                dst_pos += 1
        new_template = []
        dst_pos = 0
        for i, part_variants in enumerate(multi_template):
            if not new_template:
                new_template += part_variants
            else:
                tmp = []
                for prev in new_template:
                    for next in part_variants:
                        new = prev + next
                        tmp.append(new)
                new_template = deepcopy(tmp)
            if i < len(multi_template) - 1:
                for j, arr in enumerate(new_template):
                    new_template[j].append(dsts[dst_pos])
                dst_pos += 1
        return new_template

    @classmethod
    def compile_composed_templates(cls, raw):
        """
        Переводит строки с расстоянием в список объектов регулярных выражений
        atr raw: текст, исходные строки разделённые '\n'
        return: список шаблонов с дистанцией в формате программы МСМ
        """
        made = []
        lines = raw.split(u'\n')
        for line in lines:
            line = line.strip()
            if line == '':
                continue
            arr = line.split(u';')
            case_sensitive = int(arr[-1])
            template = arr[:-1]
            if case_sensitive:
                flags = 0
            else:
                flags = re.I+re.U
            d = {}
            d['re'] = [re.compile(p.replace(u'$&777', u';'), flags) for p in template]
            made.append(d)

        return made

    @classmethod
    def create_unique_compile(cls, gotov, template, used, flag):
        """
        Создает список скомпилированных строк из списка шаблонов
        atr gotov: пустой список скомпил.шаблонов
        atr template: шаблон
        atr used: использованные преобразования
        atr flag: есть ли регистр
        return: скомпилированный список
        """
        for p in template.split(u';'):
            is_in = 0
            for el in used:
                if el.template == p.replace(u'$&777', u';'):
                    if el.flags == flag:
                        gotov.append(el)
                        is_in = 1
                        break
            if not is_in:
                new = re.compile(p.replace(u'$&777', u';'), flag)
                gotov.append(new)
                used.append(new)
        return gotov

    @classmethod
    def compile_single_templates(cls, raw):
        """
        Переводит строки без расстояния в список объектов регулярных выражений
        atr raw: текст, исходные строки разделённые '\n'
        return: список одиночных шаблонов в формате программы МСМ
        """
        made = []
        lines = raw.split(u'\n')
        for line in lines:
            line = line.strip()
            if line == '':
                continue
            arr_raw = line.split(u';')
            arr = []
            for el in arr_raw:
                el = el.replace(u'$&777', u';')
                arr.append(el)
            case_sensitive = int(arr[-1])
            template = u';'.join(arr[:-1])
            d = {}
            if case_sensitive:
                flags = 0
            else:
                flags = re.I+re.U
            d['re'] = re.compile(template.replace(u'$&777', u';'), flags)
            d['case_sensitive'] = case_sensitive
            made.append(d)
        return made

    @classmethod
    def sobrat_rasst_for_tree_form(cls, rasst_template, flag, all_templates):
        """
        Создает дерево из списка шаблонов с дистанцией.
        atr rasst_template: отдаленный паттерн (формат списка)
        atr flag: если флаг чувствителен к регистру
        atr all_templates: словарь, скомпилированные ключи, значения индексы шаблонов
        return: формирует шаблон с индексами
        """
        made = []
        for i, p in enumerate(rasst_template):
            if i%2:
                made.append(p)
            else:
                made.append(all_templates[p])
        return made

    @classmethod
    def sobrat_rasst_re(cls, arr, flag):
        """
         Преобразует список шаблонов в необработанный формат - без метасимволов, формат со скомпилированными частями
         atr arr: шаблон шаблон с дистанцией
         atr flag: есть ли дистанция или нет
         return: список скомпилированных шаблонов с кортежными расстояниями, список необработанных шаблонов, список необработанных шаблонов для эластика
         """
        made = []
        raw = []
        iter = 0
        start = 0
        for p in arr:
            if iter == 0:
                made.append(re.compile(p, flag))
                raw.append(p)
                iter += 1
            elif iter == 1:
                start = int(p)
                iter += 1
            elif iter == 2:
                end = int(p)
                pair = (start, end)
                made.append(pair)
                iter = 0

        return made, raw

    @classmethod
    def redact_template(cls, template):
        """
        Удаляет метасимволы из регулярого выражения
        atr template: шаблон с метасимволами
        return: очищенный от метасимволов
        """
        arr_raw = template.split(u';')
        arr = []
        for el in arr_raw:
            arr.append(el.replace(u'$&777', u';'))
        new = []
        new_full = []
        for part in arr:
            if part == '':
                pass
            else:
                if part == u'^ $' or part == u' ':
                    new.append(u' ')
                    new_full.append(u' ')
                    continue
                if u'^' == part[0]:
                    part = part[1:]
                if part == u'$':
                    pass
                elif part == u'^\$$' or part == u'\$$':
                    part = u'\$'
                elif part[-1] == u'$':
                    if part[-2].isalpha():
                        part = part[:-1]
                    elif part[-2] == u'\\':
                        pass
                    else:
                        part = part[:-1]

                new.append(part)
                new_full.append(part)
        n_new = []
        for el in new:
            n_new.append(el.replace(u';', u'$&777'))
        joined = u''.join(new_full)
        joined = joined.lower()
        return ';'.join(n_new), joined

    @classmethod
    def perehod_label_hdbks(cls, label, hdbk_types):
        """
        Компилирует шаблоны справочник в объекты регулярных выражений
         arg label: справочник строк
         arg hdbk_types: список типов строк этого справочника (например, composed_kluch, single_iskl и т. д.)
         return: список строк скомпилированного справочника
        """
        try:
            label['rules'] = json.loads(label['rules'])
        except KeyError:
            pass

        try:
            label['excluded_sources'] = json.loads(label['excluded_sources'])
        except KeyError:
            label['excluded_sources'] = []

        for hdbk_type in hdbk_types:
            if hdbk_type in label:
                if 'composed' in hdbk_type:
                    label[hdbk_type] = cls.compile_composed_templates(label[hdbk_type])
                elif 'rasst' in hdbk_type:
                    label[hdbk_type] = cls.compile_rasst_templates(label[hdbk_type])
                elif 'single' in hdbk_type:
                    label[hdbk_type] = cls.compile_single_templates(label[hdbk_type])
            else:
                label[hdbk_type] = []

    @classmethod
    def perehod_to_html_symb(cls, template):
        """
        Замена метасимволов на html формат
        arg template:старая строка
        return: новая строка
        """
        if u'\\' not in template:
            return template
        arr = []
        standalone = []
        for i, letter in enumerate(template):
            if u'\\' not in template[i:]:
                if not arr:
                    arr.append(template[i:])
                else:
                    if len(arr) - 1 not in standalone:
                        arr[-1] += template[i:]
                    else:
                        arr.append(template[i:])
                break
            if letter == u'\\':
                if not arr:
                    arr.append(letter)
                    standalone.append(0)
                else:
                    if len(arr) - 1 not in standalone:
                        arr.append(letter)
                        new = len(arr) - 1
                        standalone.append(new)
                    else:
                        if arr[-1] == u'\\':
                            arr[-1] += letter
                        else:
                            arr.append(letter)
                            new = len(arr) - 1
                            standalone.append(new)
            else:
                if not arr:
                    arr.append(letter)
                else:
                    if len(arr) - 1 not in standalone:
                        arr[-1] += letter
                    else:
                        if arr[-1] == u'\\' and letter in obj_zamen['all_symbols']:
                            arr[-1] += letter
                        else:
                            arr.append(letter)

        for i, el in enumerate(arr):
            if u'\\' in el:
                for obj in obj_zamen['objects']:
                    arr[i] = arr[i].replace(obj[1], obj[0])

        template = u''.join(arr)
        return template

    @classmethod
    def perehod_from_html_symb(cls, template):
        if u'&#' not in template:
            return template
        for obj in obj_zamen['objects']:
            template = template.replace(obj[0], obj[1])
        return template

    @classmethod
    def zamen_slash_in_parts(cls, arr):
        for j, el in enumerate(arr):
            if isinstance(el, j) and u'\\' in el:
                for obj in obj_zamen['objects_elastic_exceptions_double']:
                    arr[j] = arr[j].replace(obj[1], obj[0])
            elif isinstance(el, dict) and el.kluchs()[0] == 'ro':
                arr[j]['ro'] = cls.zamen_slash_in_parts(el['ro'])
        return arr

    @classmethod
    def perehod_from_html_elastic_exceptions_symb(cls, template):
        if u'&#' not in template:
            return template
        for obj in obj_zamen['objects_elastic_exceptions']:
            template = template.replace(obj[0], obj[1])
        return template

print(transform.redact_template('^солнце$;^ $;^поднимается$'), '- проверка')