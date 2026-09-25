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
| `pantalla.html` | Pantalla del local (TV): rota promos, menú y fotos; reloj, estado y QR de WhatsApp |
| `css/pantalla.css` / `js/pantalla.js` | Estilos y lógica de la pantalla del local |
| `js/datos.js` | Datos compartidos: `MENU`, `PROMOS` y `FOTOS_REDES` (los usan la landing y la pantalla) |
| `css/styles.css` | Estilos, tokens de color y las duraciones de movimiento (`--dur-*`) |
| `js/app.js` | Filtro del menú, menú móvil, carrusel de promos y animaciones por scroll |
| `img/` | Fotos optimizadas en WebP, logo, stickers del panda, favicon e imagen para compartir (`og.jpg`) |
| `img/vaso/` | Secuencia del vaso 3D: `g/` 1000x1250 y `c/` 600x750, cuadros `00`-`80` |
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

Editar el arreglo `MENU` en `js/datos.js` (también alimenta la pantalla del local). Cada producto lleva
`cat` (categoría; los filtros salen solos de las categorías que existan),
`name`, `desc`, `price`, `img` (nombre del archivo en `img/` sin extensión)
y `pos` (encuadre de la foto, `object-position`). `ing` es la lista de
ingredientes que aparece al pasar el mouse por la foto (en táctil, con el
botón "i"); PENDIENTE validarla con el cliente.

Si un producto no tiene foto propia, `img: null`: la tarjeta muestra el panda
con "Foto pronto". Mejor eso que repetir la foto de otro producto. Hoy están
así Mango, Matcha, Café con leche, Capuchino, Chocolate caliente, Frozen Chai
y Dim sum; Fresas Dubái usa el afiche general de fresas (`pc_22`).

## Cambiar o agregar fotos

1. Poner el original en la carpeta de originales (fuera del repo): la carpeta
   `assets/` del handoff de diseño, que además tiene el logo y los pandas.
2. Agregarlo al diccionario `FOTOS` de `tools/optimizar-imagenes.py` con su
   ancho máximo, o a `RECORTES` si la tarjeta necesita solo una parte del afiche.
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
  El tramo fijo es 160 % de pantalla en escritorio y 110 % en teléfonos; el
  vaso termina al 78 % (`ANIM_FIN`) y el resto lo deja quieto antes de soltar.
  Un bucle con lerp (0,09 PC / 0,08 táctil) suaviza el scroll y el `<canvas>`
  mezcla los dos cuadros vecinos; los pasos, las etiquetas y el disco
  (`--s1`, `--s2`, `--s3`) leen ese mismo valor suavizado.
- Los cuadros se descargan cuando la sección se acerca: `img/vaso/g`
  (1000x1250, 3,1 MB) si el vaso se pinta a más de 600 px reales
  (densidad tope 2, así que también la mayoría de los teléfonos) y
  `img/vaso/c` (600x750, 1,5 MB) en pantallas chicas. Con "ahorro de datos"
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

Funciona con Blender 4.2 y 5.x. La secuencia publicada (81 cuadros a
1000x1250, 64 muestras, con profundidad de campo) se renderizó con 5.2;
`vaso.blend` está guardado con 4.2 y abre en las dos (si se vuelve a guardar
con `--blend` desde 5.x, ya no abre en 4.2). Para regenerar la secuencia
(unas 2 horas con CPU en una laptop de 6 núcleos):

```bash
blender -b -P tools/vaso-3d/vaso.py -- --out render --blend tools/vaso-3d/vaso.blend
python tools/vaso-3d/exportar.py render
```

`tools/vaso-3d/vaso.blend` es la escena ya armada (con el logo empacado)
para abrirla y retocarla en Blender; `--blend` la vuelve a guardar. Para probar
cambios rápido: `--frames 0,120,240 --samples 24 --scale 50`. Los tiempos
de cada paso están en las constantes `F_*` de `vaso.py`; si cambian,
actualizar los tramos de `escribirPasos()` en `app.js`. `render/` no se
versiona.

## Pantalla del local (TV)

`pantalla.html` es la señalización para las tres TV de 32". En el navegador
de la TV (o de un stick/mini PC conectado) se abre
`https://jcanalyticscr.github.io/placeres-culposos-web/pantalla.html` y se
toca "Pantalla completa" (o la tecla F). Rota sola: menú por categoría,
promos del mes, la estrella de la casa y una invitación a seguir en redes;
a la derecha, hora y fecha en vivo, abierto/cerrado según el horario, una
foto de redes que va cambiando y el QR para pedir por WhatsApp desde la mesa.

Parámetros en la URL:

| Parámetro | Efecto |
|---|---|
| `?v=1` | Versión vertical (franja arriba), para una TV de pie |
| `?seg=12` | Segundos por diapositiva (por defecto 9) |
| `?sinboton` | Oculta el botón de pantalla completa (modo kiosco) |

Se combinan: `pantalla.html?v=1&seg=12&sinboton`. El horario de
abierto/cerrado está en `HORARIO` dentro de `js/pantalla.js` (PENDIENTE:
confirmar con el cliente). Sin internet la TV no carga la página: dejar la
pestaña abierta y el navegador se encarga de la caché.

## Pendientes antes de lanzar

- [ ] Confirmar el horario con el cliente (1:00 a 9:00 p. m. es un marcador).
- [ ] Validar precios y descripciones del menú. Solo son reales los de los
      afiches: fresas ₡2.000, 2x fresas ₡4.000, 2 milkshakes ₡4.500,
      2x ensalada de frutas ₡5.000, 2x bubble tea ₡5.000.
- [ ] Enlaces de Facebook y PedidosYa en el footer.
- [ ] Reemplazar las fotos por las de la sesión de producto cuando exista.
- [ ] Quitar `<meta name="robots" content="noindex">` de `index.html`.
- [ ] Dominio propio: agregar `CNAME` y actualizar las URL de `og:image` y del JSON-LD.
