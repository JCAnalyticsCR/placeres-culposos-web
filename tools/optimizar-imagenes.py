"""Convierte las fotos originales del cliente en los WebP livianos de img/.

Uso:
    python tools/optimizar-imagenes.py "<carpeta con los originales>"

Los originales NO se versionan (pesan 300-500 KB cada uno); viven en la
carpeta del handoff de diseño. Este script es la única vía para regenerar
img/: si cambia una foto, se reemplaza el original y se vuelve a correr.
"""

import sys
from pathlib import Path

from PIL import Image

DESTINO = Path(__file__).resolve().parent.parent / "img"

# nombre original -> (ancho máximo, calidad). El ancho sale del tamaño
# pintado más grande de cada foto x2 (pantallas retina).
FOTOS = {
    "pc_01.jpg": (640, 78),  # TikTok 9:16 (pc_01 también va en el menú)
    "pc_02.jpg": (640, 78),
    "pc_18.jpg": (640, 78),
    "pc_07.jpg": (800, 76),  # promo + menú
    "pc_14.jpg": (700, 76),  # tarjetas de menú
    "pc_15.jpg": (700, 76),
    "pc_16.jpg": (640, 78),
    "pc_17.jpg": (700, 76),
    "pc_20.jpg": (700, 76),
    "pc_21.jpg": (700, 76),
    "pc_23.jpg": (700, 76),
    "pc_25.jpg": (700, 76),
    "pc_26.jpg": (700, 76),
    "pc_27.jpg": (700, 76),
    "pc_28.jpg": (700, 76),
    "pc_30.jpg": (700, 76),
    "pc_31.jpg": (700, 76),
    "pc_34.jpg": (700, 76),
    "pc_35.jpg": (700, 76),
    "pc_10.jpg": (1200, 74),  # foto del local, ubicación
}

# El hero lleva dos tamaños (srcset): teléfono y escritorio.
HERO = ("pc_29.jpg", [(600, 78), (1100, 76)])

# Recortes con transparencia.
STICKERS = {
    "panda-tea.png": 340,
    "panda-happy.png": 330,
}


def reducir(im: Image.Image, ancho: int) -> Image.Image:
    if im.width <= ancho:
        return im
    alto = round(im.height * ancho / im.width)
    return im.resize((ancho, alto), Image.LANCZOS)


def guardar_webp(im: Image.Image, nombre: str, calidad: int) -> None:
    ruta = DESTINO / nombre
    im.save(ruta, "WEBP", quality=calidad, method=6)
    print(f"{nombre:<24} {im.width}x{im.height}  {ruta.stat().st_size // 1024} KB")


def main(origen: Path) -> None:
    DESTINO.mkdir(exist_ok=True)

    for nombre, (ancho, calidad) in FOTOS.items():
        im = Image.open(origen / nombre).convert("RGB")
        guardar_webp(reducir(im, ancho), Path(nombre).stem + ".webp", calidad)

    nombre, tamanos = HERO
    im = Image.open(origen / nombre).convert("RGB")
    for ancho, calidad in tamanos:
        guardar_webp(reducir(im, ancho), f"{Path(nombre).stem}-{ancho}.webp", calidad)

    # Imagen para compartir (WhatsApp/Facebook): 1200x630 JPEG, recorte al centro
    # de las fresas. JPEG porque algunos scrapers aún no leen WebP.
    og = reducir(im, 1200)
    arriba = round(og.height * 0.58 - 315)
    og = og.crop((0, arriba, 1200, arriba + 630))
    og.save(DESTINO / "og.jpg", "JPEG", quality=80, optimize=True, progressive=True)
    print(f"{'og.jpg':<24} 1200x630  {(DESTINO / 'og.jpg').stat().st_size // 1024} KB")

    for nombre, ancho in STICKERS.items():
        im = Image.open(origen / nombre).convert("RGBA")
        guardar_webp(reducir(im, ancho), Path(nombre).stem + ".webp", 86)

    logo = Image.open(origen / "logo-pc.png").convert("RGBA")
    guardar_webp(reducir(logo, 192), "logo.webp", 88)
    reducir(logo, 180).save(DESTINO / "apple-touch-icon.png", optimize=True)
    reducir(logo, 64).save(DESTINO / "favicon.png", optimize=True)
    print("apple-touch-icon.png, favicon.png")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
