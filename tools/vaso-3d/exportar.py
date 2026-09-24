"""Convierte los PNG de `vaso.py` en la secuencia WebP que usa la web.

Uso:
    python tools/vaso-3d/exportar.py <carpeta con f000.png ... f240.png>

Genera, con fondo transparente (el disco blanco y el rosado los pone el CSS):
    img/vaso/g/00.webp ... 60.webp   800x1000, pantallas grandes y retina
    img/vaso/c/00.webp ... 60.webp   480x600, teléfonos

`js/app.js` (VASO_CUADROS) asume 61 cuadros numerados 00-60: si cambia la
cantidad de cuadros, actualizar esa constante.
"""

import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

DESTINO = Path(__file__).resolve().parents[2] / "img" / "vaso"
TAMANOS = {"g": (800, 1000, 70), "c": (480, 600, 72)}  # carpeta -> (ancho, alto, calidad)


def mascara_bordes(tam):
    """Alfa que se desvanece hacia los bordes del cuadro. La sombra del piso
    llega hasta el borde del render y sin esto se vería el rectángulo.
    Los márgenes no tocan el vaso (ocupa del 30 % al 70 % del ancho y llega
    hasta el 92 % del alto); arriba solo se suavizan las fresas que entran."""
    w, h = tam
    m = Image.new("L", tam, 0)
    ImageDraw.Draw(m).rectangle((int(w * 0.1), int(h * 0.02), int(w * 0.9), int(h * 0.98)), fill=255)
    return m.filter(ImageFilter.GaussianBlur(w * 0.03))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    origen = Path(sys.argv[1])
    pngs = sorted(origen.glob("f[0-9][0-9][0-9].png"))
    if not pngs:
        sys.exit(f"No hay cuadros f###.png en {origen}")

    total = {k: 0 for k in TAMANOS}
    for carpeta in TAMANOS:
        (DESTINO / carpeta).mkdir(parents=True, exist_ok=True)
        for viejo in (DESTINO / carpeta).glob("*.webp"):
            viejo.unlink()

    mascara = None
    for i, png in enumerate(pngs):
        im = Image.open(png).convert("RGBA")
        mascara = mascara or mascara_bordes(im.size)
        im.putalpha(ImageChops.multiply(im.getchannel("A"), mascara))
        for carpeta, (w, h, q) in TAMANOS.items():
            salida = DESTINO / carpeta / f"{i:02d}.webp"
            im.resize((w, h), Image.LANCZOS).save(
                salida, "WEBP", quality=q, alpha_quality=80, method=6)
            total[carpeta] += salida.stat().st_size

    for carpeta, bytes_ in total.items():
        print(f"{carpeta}: {len(pngs)} cuadros, {bytes_ / 1024:.0f} KB en total")


if __name__ == "__main__":
    main()
