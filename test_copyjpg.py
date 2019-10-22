import os
from PIL import Image

THUMB_SIZE = (300, 200)


def copyjpg(origem, destino):
    pil_image = Image.open(origem)
    #  Mantain ratio
    print(THUMB_SIZE)
    size = pil_image.size
    print(size)
    new_size = (int(THUMB_SIZE[1] / size[1] * size[0]), THUMB_SIZE[1])
    pil_image.thumbnail(new_size, Image.ANTIALIAS)
    print(pil_image.size)
    pil_image.save(destino)


for arquivo in os.listdir('images_test'):
    origem = os.path.join('images_test', arquivo)
    destino = os.path.join('images_test_resize', arquivo)
    copyjpg(origem, destino)
