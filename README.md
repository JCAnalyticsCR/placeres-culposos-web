# Placeres Culposos CR · Sitio web

Landing de Placeres Culposos CR, heladería y cafetería en El Roble,
Puntarenas (frente a Coopenae). Muestra el menú y las promos del mes, y
lleva a pedir por WhatsApp.

Publicado en https://jcanalyticscr.github.io/placeres-culposos-web/

## Stack

HTML, CSS y JavaScript sin paso de compilación ni dependencias. Tipografías
Anton y Poppins desde Google Fonts. Sin servidor, base de datos ni
formularios: los pedidos se hacen por WhatsApp.

## Estructura

| Archivo | Contenido |
|---|---|
| `index.html` | Página única con todas las secciones |
| `css/styles.css` | Estilos, tokens de color y las duraciones de movimiento (`--dur-*`) |
| `js/app.js` | Datos del menú (`MENU`), filtro, menú móvil, carrusel de promos y animaciones por scroll |
| `img/` | Fotos optimizadas en WebP, logo, stickers del panda, favicon e imagen para compartir (`og.jpg`) |
| `img/vaso/` | Secuencia del vaso 3D: `g/` 800x1000 y `c/` 480x600, cuadros `00`-`60` |
| `tools/optimizar-imagenes.py` | Regenera `img/` a partir de las fotos originales |
| `tools/vaso-3d/` | Escena de Blender del vaso (`vaso.py`) y exportador de la secuencia (`exportar.py`) |

## Correr en local

```bash
python -m http.server 8000
```

y abrir http://localhost:8000.

## Publicación

GitHub Pages desde la rama `main` (raíz). Cada push a `main` publica en uno
o dos minutos.

## Cambiar el menú

Editar el arreglo `MENU` al inicio de `js/app.js`. Cada producto lleva
`cat` (categoría; los filtros salen solos de las categorías que existan),
`name`, `desc`, `price`, `img` (nombre del archivo en `img/` sin extensión)
y `pos` (encuadre de la foto, `object-position`).

## Cambiar o agregar fotos

1. Poner el original en la carpeta de originales (fuera del repo).
2. Agregarlo al diccionario `FOTOS` de `tools/optimizar-imagenes.py` con su ancho máximo.
3. Correr:

```bash
python tools/optimizar-imagenes.py "<carpeta de originales>"
```

Requiere Pillow (`pip install -r tools/requirements.txt`).

## Versionado de CSS y JS

`index.html` carga los estilos y el script con `?v=<fecha><letra>` (por
ejemplo `styles.css?v=20260924a`). Cada vez que cambie un `.css` o `.js`,
actualizá ese código antes de publicar para que los navegadores, sobre todo
Safari en iPhone, no mezclen la página nueva con archivos viejos guardados.

## Movimiento

- Sección de fresas: la vista queda fija (sticky) mientras se hace scroll y
  el vaso 3D se arma en tres pasos (fresas, crema, leche condensada).
  `app.js` calcula el progreso, pinta en el `<canvas>` el cuadro que toca y
  escribe `--s1`, `--s2` y `--s3` para los pasos, las etiquetas y el disco.
- Los cuadros se descargan cuando la sección se acerca (unos 2 MB en
  pantallas grandes, menos de 1 MB en teléfonos). Con "ahorro de datos"
  no se descargan y se ve la foto del vaso terminado.
- La vista fija necesita al menos 600 px de alto; en teléfonos acostados el
  vaso se arma igual, pero sin fijar la sección.
- Parallax del hero solo en pantallas de 768 px o más.
- Con "reducir movimiento" activado no hay parallax, el panda no se mueve,
  la sección no se fija y el vaso aparece terminado.
- Sin JavaScript el contenido se ve completo (el vaso aparece terminado).

## Vaso 3D (Blender)

El vaso se modela y renderiza por código en `tools/vaso-3d/vaso.py`: vaso
PET con labio, sticker con `img/logo.webp`, mitades de fresa con semillas y
corte, crema, copete de crema batida, leche condensada y la fresa de arriba.
Las mitades caen con física real (Bullet); su posición final queda guardada
en `tools/vaso-3d/reposo.json` para que cada render dé el mismo vaso.

Requiere Blender 4.2 (o `pip install bpy==4.2.0` con Python 3.11). Para
regenerar la secuencia (unos 50 min en 4 núcleos):

```bash
blender -b -P tools/vaso-3d/vaso.py -- --out render --blend tools/vaso-3d/vaso.blend
python tools/vaso-3d/exportar.py render
```

`tools/vaso-3d/vaso.blend` es la escena ya armada (con el logo empacado)
para abrirla y retocarla en Blender; `--blend` la vuelve a guardar. Para probar
cambios rápido: `--frames 0,120,240 --samples 24 --scale 50`. Los tiempos
de cada paso están en las constantes `F_*` de `vaso.py`; si cambian,
actualizar los tramos de `escribirVaso()` en `app.js`. `render/` no se
versiona.

## Pendientes antes de lanzar

- [ ] Confirmar el horario con el cliente (1:00 a 9:00 p. m. es un marcador).
- [ ] Validar precios y descripciones del menú. Solo son reales los de los
      afiches: fresas ₡2.000, 2x fresas ₡4.000, 2 milkshakes ₡4.500,
      2x ensalada de frutas ₡5.000, 2x bubble tea ₡5.000.
- [ ] Enlaces de Facebook y PedidosYa en el footer.
- [ ] Reemplazar las fotos por las de la sesión de producto cuando exista.
- [ ] Quitar `<meta name="robots" content="noindex">` de `index.html`.
- [ ] Dominio propio: agregar `CNAME` y actualizar las URL de `og:image` y del JSON-LD.
