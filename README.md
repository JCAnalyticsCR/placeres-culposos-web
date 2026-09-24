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
| `tools/optimizar-imagenes.py` | Regenera `img/` a partir de las fotos originales |

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

- El vaso de fresas se arma con el scroll: `app.js` calcula el progreso de
  la sección y escribe `--s1`, `--s2` y `--s3`; todo lo demás es CSS.
- Parallax del hero solo en pantallas de 768 px o más.
- Con "reducir movimiento" activado no hay parallax, el panda no se mueve y
  el vaso aparece terminado.
- Sin JavaScript el contenido se ve completo (el vaso aparece terminado).

## Pendientes antes de lanzar

- [ ] Confirmar el horario con el cliente (1:00 a 9:00 p. m. es un marcador).
- [ ] Validar precios y descripciones del menú. Solo son reales los de los
      afiches: fresas ₡2.000, 2x fresas ₡4.000, 2 milkshakes ₡4.500,
      2x ensalada de frutas ₡5.000, 2x bubble tea ₡5.000.
- [ ] Enlaces de Facebook y PedidosYa en el footer.
- [ ] Reemplazar las fotos por las de la sesión de producto cuando exista.
- [ ] Quitar `<meta name="robots" content="noindex">` de `index.html`.
- [ ] Dominio propio: agregar `CNAME` y actualizar las URL de `og:image` y del JSON-LD.
