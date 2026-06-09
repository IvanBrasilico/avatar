import sys
if '.' not in sys.path:
    sys.path.insert(0, '.')
import os
import xml.etree.ElementTree as ET

import chardet

from avatar.utils.conf import TAGS_DATA, TAGS_NUMERO
from avatar.utils.logconf import logger


def get_numero_data(root, root_tag):
    numero = None
    data = None
    for tag in root.iter(root_tag + 'attribute'):
        tagname = tag.attrib.get('name')
        if tagname and tagname in TAGS_NUMERO:
            numero = tag.text
            logger.debug('get_numero_data - attribute %s - %s' %
                         (str(tagname), str(numero)))
    for atag in TAGS_NUMERO:
        for tag in root.iter(root_tag + atag):
            logger.debug(tag)
            lnumero = tag.text
            if lnumero is not None:
                logger.debug('get_numero_data - %s - %s' % (atag, lnumero))
                numero = lnumero.replace('?', 'X')
                break
    for atag in TAGS_DATA:
        for tag in root.iter(root_tag + atag):
            data = tag.text
            if data is not None:
                break
    if numero:
        numero = numero.strip()
    return numero, data


def le_xml_legado(xml_content):
    try:
        root = ET.fromstring(xml_content)
    except Exception:
        return None
    root_tag = ""
    if root.tag.find("}") != -1:
        root_tag = root.tag.split("}")[0] + "}"

    numero, data = get_numero_data(root, root_tag)
    truckid = 'NI'
    operador = 'NI'
    alerta = False
    for tag in root.iter(root_tag + 'TruckId'):
        truckid = tag.text
    for tag in root.iter(root_tag + 'Login'):
        operador = tag.text
    for tag in root:
        for t in tag:
            if t.text == 'AL':
                alerta = True
    return numero, data, truckid, operador, alerta


def extract_data_from_xml(xml_content):
    try:
        root = ET.fromstring(xml_content)
    except Exception:
        return None

    ns = None
    if root.tag.startswith('{'):
        ns_uri = root.tag.split('}')[0].strip('{')
        ns = {'ns': ns_uri}
    else:
        ns = {}

    def find_text(elem, path):
        if ns:
            res = elem.find(path, ns)
        else:
            res = elem.find(path)
        return res.text if res is not None and res.text else None

    def findall(elem, path):
        if ns:
            return elem.findall(path, ns)
        return elem.findall(path)

    date = find_text(root, 'ns:Date' if ns else 'Date')
    truck_id = find_text(root, 'ns:TruckId' if ns else 'TruckId')

    plate_number = None
    vehicle_path = 'ns:AdminData/ns:Vehicle' if ns else 'AdminData/Vehicle'
    vehicle_elem = root.find(vehicle_path, ns) if ns else root.find('AdminData/Vehicle')
    if vehicle_elem is not None:
        plate_number = find_text(vehicle_elem, 'ns:PlateNumber' if ns else 'PlateNumber')

    container_ids = []
    trailers_path = 'ns:AdminData/ns:Vehicle/ns:Trailers/ns:Trailer' if ns else 'AdminData/Vehicle/Trailers/Trailer'
    trailers = findall(root, trailers_path)
    for trailer in trailers:
        containers_path = 'ns:Containers/ns:Container' if ns else 'Containers/Container'
        containers = findall(trailer, containers_path)
        for container in containers:
            cid = find_text(container, 'ns:ContainerId' if ns else 'ContainerId')
            if cid:
                container_ids.append(cid)

    login_list = []
    operations_path = 'ns:Operations/ns:Operation' if ns else 'Operations/Operation'
    operations = findall(root, operations_path)
    for op in operations:
        login = find_text(op, 'ns:Login' if ns else 'Login')
        if login:
            login_list.append(login)

    return {
        'Date': date,
        'TruckId': truck_id,
        'PlateNumber': plate_number,
        'ContainerIds': container_ids,
        'Logins': login_list
    }


def extract_manifest_data(xml_content):
    root = ET.fromstring(xml_content)
    # Extrai informações principais
    result = {}
    result['accession'] = root.findtext('accession')
    result['system'] = root.findtext('system')
    result['createdate'] = root.findtext('createdate')
    result['exportdate'] = root.findtext('exportdate')
    # Extrai containers dos atributos
    container1 = None
    container2 = None
    for attr in root.find('attributes'):
        if attr.attrib.get('name') == "Container1":
            container1 = attr.text
        if attr.attrib.get('name') == "Container2":
            container2 = attr.text
    result['Container1'] = container1
    result['Container2'] = container2
    return result


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)  # lê parte do arquivo para análise
        result = chardet.detect(raw_data)
        return result['encoding']


def extract_from_any_xml(path):
    numero = None
    data = None
    truckid = None
    operador = None
    alerta = None
    with open(path, 'r', encoding=detect_encoding(path)) as f:
        xml_content = f.read()
    root = ET.fromstring(xml_content)
    if root.tag == 'manifest':
        logger.debug('----- manifest -----')
        manifest_data = extract_manifest_data(xml_content)
        logger.debug(manifest_data)
        numero = manifest_data.get('Container1')
        data = manifest_data.get('createdate')
        truckid = manifest_data.get('acession')
        operador = manifest_data.get('')
        # A priori, esta informação de alerta não é utilizada, pois é extraída depois do XML no
        # virasana_periodic
        alerta = False
    elif root.tag.endswith('DataForm'):
        logger.debug('----- DataForm -----')
        dataform_data = extract_data_from_xml(xml_content)
        logger.debug(dataform_data)
        numero = dataform_data.get('ContainerIds')[0]
        data = dataform_data.get('Date')
        truckid = dataform_data.get('TruckId')
        operador = dataform_data.get('Logins')[0]
        # A priori, esta informação de alerta não é utilizada, pois é extraída depois do XML no
        # virasana_periodic
        alerta = False
    else:
        logger.debug('----- le_xml_legado -----')
        numero, data, truckid, operador, alerta = le_xml_legado(xml_content)

    return numero, data, truckid, operador, alerta



