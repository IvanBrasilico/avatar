import os
import sys

sys.path.append('.')

from avatar.utils.le_xmlv2 import extract_from_any_xml

conteudo_dos_arquivos = {
    "202511010026120014.xml": ('SIMU2611593', '2025-11-01T07:29:30.417Z', '202511010026120014', 'Guilherme Jesus',
                               False),
    "202511010026120017.xml": ('AAMU2630984', '2025-11-01T07:39:36.540Z', '202511010026120017', 'rodrigo andrade',
                               False),
    "202511070026910018.xml": ('CRXU8691490', '2025-11-07T06:19:23.200Z', '202511070026910018', 'EBCO.ROGER', False),
    "202511070026910215.xml": ('BEAU2201110', '2025-11-07T11:18:28.083Z', '202511070026910215', 'I.ALVES', False),
    "20251110002613000O.xml": ('TRHU7151369', '2025-11-10T04:45:48.060Z', '20251110002613000O', 'EBCO.ROGER', False),
    "202511100026130029.xml": ('MRSU8634775', '2025-11-10T05:49:36.550Z', '202511100026130029', 'EBCO.ROGER', False),
    "202511110026300004.xml": ('TIIU4543422', '2025-11-11T18:42:11.340Z', '202511110026300004', 'L.LIMA', False),
    "202511110026300005.xml": ('MSNU5728513', '2025-11-11T18:42:56.780Z', '202511110026300005', 'L.LIMA', False),
    "20251112000000000148145.xml": ('BMOU1387370', '2025-11-12T04:29:10Z', None, None, False),
    "20251112000000000148377.xml": ('HASU5096871', '2025-11-12T16:18:57Z', None, None, False),
    "20251112002621005X.xml": ('FCIU7093520', '2025-11-12T08:04:03.113Z', '20251112002621005X', 'Jacilene', False),
    "20251112002621006D.xml": ('CXTU1135533', '2025-11-12T09:32:28.097Z', '20251112002621006D', 'JESSICA S.', False),
    "202511120026900030.xml": ('MNBU0435706', '2025-11-12T03:35:25.317Z', '202511120026900030', 'EBCO.ALLAN', False),
    "202511120026900156.xml": ('MEDU6187268', '2025-11-12T07:42:34.470Z', '202511120026900156', 'EBCO.ALLAN', False),
    "202511120026910018.xml": ('DFSU7778749', '2025-11-12T03:36:56.420Z', '202511120026910018', 'EBCO.RYAN', False),
    "202511120026910158.xml": ('SUDU6562473', '2025-11-12T07:30:08.910Z', '202511120026910158', 'EBCO.DANIEL', False),
}
if __name__ == '__main__':
    from avatar.utils.logconf import logger

    # logger.setLevel(DEBUG)

    # Diretório com arquivos XML
    directory = 'tests/xmls_exemplo/'

    # Lista de nomes de arquivos XML (adaptar conforme seus arquivos)
    file_names = os.listdir(directory)

    # Processar todos os arquivos e comparar conteúdo extraído
    for fname in file_names:
        path = os.path.join(directory, fname)
        extracted = extract_from_any_xml(path)
        logger.debug(f'Arquivo: {fname}')
        logger.debug(f'Dados extraídos: {extracted}')

        print(f'"{fname}": {extracted},')
        assert extracted == conteudo_dos_arquivos[fname]
        logger.debug('-' * 60)
