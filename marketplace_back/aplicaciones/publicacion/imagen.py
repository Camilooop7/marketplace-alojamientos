from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework import serializers

MAXIMO_IMAGENES = 10
TAMANO_MAXIMO = 3 * 1024 * 1024
LADO_MAXIMO = 1600
FORMATOS = {'JPEG', 'PNG', 'WEBP'}


def procesar_imagen(archivo):
    if archivo.size > TAMANO_MAXIMO:
        raise serializers.ValidationError('La imagen no puede pesar más de 3 MB.')
    try:
        imagen = Image.open(archivo)
        formato = imagen.format
        imagen.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise serializers.ValidationError('El archivo no es una imagen válida.')
    if formato not in FORMATOS:
        raise serializers.ValidationError('Solo se permiten imágenes JPG, PNG o WEBP.')

    imagen = ImageOps.exif_transpose(imagen)
    if imagen.mode in ('RGBA', 'LA', 'P'):
        imagen = imagen.convert('RGBA')
        fondo = Image.new('RGB', imagen.size, (255, 255, 255))
        fondo.paste(imagen, mask=imagen.split()[-1])
        imagen = fondo
    elif imagen.mode != 'RGB':
        imagen = imagen.convert('RGB')
    imagen.thumbnail((LADO_MAXIMO, LADO_MAXIMO))

    salida = BytesIO()
    imagen.save(salida, 'JPEG', quality=85, optimize=True)
    return salida.getvalue()
