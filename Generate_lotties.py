import re
import json
import os
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import copy

class Point:
    __slots__ = ['_x', '_y', '_mode', '_x1', '_x2', '_y1', '_y2']
    
    def __init__(self, x, y, mode, x1, x2, y1, y2):
        self._x = x
        self._y = y

        self._x1 = x1
        self._x2 = x2

        self._y1 = y1
        self._y2 = y2

        self._mode = mode

    def __repr__(self):
        return f"[{self._x}, {self._y}],"


def split_by_letters(data):
    segments = re.findall(r'[A-Za-z][^A-Za-z]*', data)
    return segments


def extract_data_from_svg(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    namespaces = {'svg': 'http://www.w3.org/2000/svg', 'kvg': 'http://kanjivg.tagaini.net'}

    paths = root.findall(".//svg:path", namespaces)
    d_values = [path.attrib['d'] for path in paths if 'd' in path.attrib and (path.attrib['d'].startswith("M") or path.attrib['d'].startswith("m"))]

    ns = {'svg': 'http://www.w3.org/2000/svg', 'kvg': 'http://kanjivg.tagaini.net'}
    kanji_group = root.find(".//svg:g[@kvg:element]", ns)
    
    if kanji_group is not None:
        kanji = kanji_group.attrib.get("{http://kanjivg.tagaini.net}element")
        if kanji in [":", "?"]:
            kanji =  "forbidden"
    else:
        kanji =  "kanji"

    return d_values, kanji


def convert_to_point(data):
    points = []
    numbers = re.findall(r'-?\d+\.?\d*', data)
    numbers = [float(num) for num in numbers]

    mode = data[0]
    if mode == "M" or mode == "m":
        x = numbers[0]
        y = numbers[1]
        x1, x2, y1, y2 = 0, 0, 0, 0
        points.append(Point(x, y, mode, x1, x2, y1, y2))

    elif mode == "c" or mode == "C":
        for i in range(0, len(numbers), 6):
            x1 = numbers[i]
            y1 = numbers[i + 1]
            x2 = numbers[i + 2]
            y2 = numbers[i + 3]
            x = numbers[i + 4]
            y = numbers[i + 5]
            points.append(Point(x, y, mode, x1, x2, y1, y2))

    elif mode == "s" or mode == "S":
        x1 = 0
        y1 = 0
        x2 = numbers[0]
        y2 = numbers[1]
        x = numbers[2]
        y = numbers[3]
        points.append(Point(x, y, mode, x1, x2, y1, y2))

    else: 
        print("Commande " + mode + " inconnue détectée")
    return points


def replace_mask_values(template_data, in_tab, out_tab, positions_tab, end):
    data = copy.deepcopy(template_data)

    def recursive_replace(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and "mask" in value:
                    if "in-tab" in value:
                        obj[key] = in_tab
                    elif "out-tab" in value:
                        obj[key] = out_tab
                    elif "positions-tab" in value:
                        obj[key] = positions_tab
                    elif "end" in value:
                        obj[key] = end
                    elif "begin" in value:
                        obj[key] = end - 32
                else:
                    recursive_replace(value)
        elif isinstance(obj, list):
            for item in obj:
                recursive_replace(item)

    recursive_replace(data)
    return data


def generate_json(output_path, json_tab, nb_fr, template_data):
    data = copy.deepcopy(template_data)

    def recursive_replace(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and "mask" in value:
                    if "json-tab" in value:
                        obj[key] = json_tab
                    if "nb-fr" in value:
                        obj[key] = nb_fr
                else:
                    recursive_replace(value)
        elif isinstance(obj, list):
            for item in obj:
                recursive_replace(item)

    recursive_replace(data)

    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, separators=(',', ':'))


def extract_points(points):
    x, y = 0, 0
    tab, tab_i, tab_o = [], [], []
    tab_i.append([0, 0])
    
    last_control_x2, last_control_y2 = 0, 0
    
    for point in points:
        if point._mode == "c":  
            point._x2 = point._x2 - point._x
            point._y2 = point._y2 - point._y

            point._x += x
            point._y += y

        elif point._mode == "C":  
            point._x1 = point._x1 - x
            point._y1 = point._y1 - y

            point._x2 = point._x2 - point._x
            point._y2 = point._y2 - point._y


        elif point._mode == "s":  
            point._x2 = point._x2 - point._x
            point._y2 = point._y2 - point._y

            point._x1 = - last_control_x2
            point._y1 = - last_control_y2
            
            point._x += x
            point._y += y

        elif point._mode == "S": 
            point._x1 = - last_control_x2
            point._y1 = - last_control_y2

            point._x2 = point._x2 - point._x
            point._y2 = point._y2 - point._y


        if point._mode in ["C", "c", "S", "s"]:
            last_control_x2 = point._x2
            last_control_y2 = point._y2
        else:
            last_control_x2, last_control_y2 = 0, 0

        x, y = point._x, point._y

        tab.append([round(x, 2), round(y, 2)])

        if point._mode not in ["M", "m"]:
            tab_o.append([round(point._x1, 2), round(point._y1, 2)]) 
            tab_i.append([round(point._x2, 2), round(point._y2, 2)])  
        
    tab_o.append([0, 0])
    
    return tab, tab_i, tab_o


def generate_lottie(svg_path, line_template, mask_template):
    values, kanji = extract_data_from_svg(svg_path)
    output_path = f"lottie/{kanji}.json"

    i = 1
    datas = []
    for val in values:
        expressions = split_by_letters(val)

        points = []
        for expr in expressions:
            new_line = convert_to_point(expr)
            points.extend(new_line)

        tab, tab_i, tab_o = extract_points(points)
        end = i * 32

        data = replace_mask_values(line_template, tab_i, tab_o, tab, end)
        datas.append(data)
        i += 1

    size = len(values) * 32 + 64

    generate_json(output_path, datas, size, mask_template)


def generate(dossier="kanji"):
    print("Generation...")

    if not os.path.exists("lottie"):
        os.makedirs("lottie")

    with open("line.json", 'r', encoding='utf-8') as f:
        line_template = json.load(f)
    with open("mask.json", 'r', encoding='utf-8') as f:
        mask_template = json.load(f)

    svg_files = [
        os.path.join(dossier, fichier)
        for fichier in os.listdir(dossier)
        if os.path.isfile(os.path.join(dossier, fichier)) and fichier.endswith(".svg")
    ]

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(generate_lottie, path, line_template, mask_template) for path in svg_files]
        for future in futures:
            future.result()
    print("Finished")



if __name__ == "__main__":
    generate()
