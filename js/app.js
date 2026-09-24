/* Placeres Culposos CR — comportamiento de la landing.
   Sin dependencias. Todo el movimiento es CSS; este archivo solo calcula
   valores a partir del scroll y los escribe como custom properties. */

'use strict';

/* ---------- Datos del menú ----------
   PENDIENTE: validar con el cliente. Solo son reales los precios de los
   afiches (fresas tradicionales ₡2.000 y las promos 2x). `img` es el nombre
   en img/ sin extensión; `pos` es el object-position del recorte. */
const MENU = [
  { cat: 'Fresas con crema', name: 'Tradicionales', desc: 'Fresas, crema y leche condensada', price: '₡2.000', img: 'pc_29-600', pos: '50% 55%' },
  { cat: 'Fresas con crema', name: 'Con chocolate', desc: 'Crema y chocolate derretido', price: '₡2.500', img: 'pc_14', pos: '50% 50%' },
  { cat: 'Fresas con crema', name: 'Fresas Dubái', desc: 'Pistacho, kunafa y chocolate', price: '₡3.500', img: 'pc_01', pos: '50% 50%' },
  { cat: 'Fresas con crema', name: 'Rosadas con chocolate', desc: 'Edición especial', price: '₡3.000', img: 'pc_25', pos: '50% 55%' },
  { cat: 'Bubble Tea', name: 'Taro', desc: 'Con perlas de tapioca', price: '₡2.500', img: 'pc_27', pos: '50% 55%' },
  { cat: 'Bubble Tea', name: 'Fresa', desc: 'Con perlas de tapioca', price: '₡2.500', img: 'pc_35', pos: '50% 30%' },
  { cat: 'Bubble Tea', name: 'Mango', desc: 'Con perlas de tapioca', price: '₡2.500', img: 'pc_27', pos: '30% 55%' },
  { cat: 'Bubble Tea', name: 'Matcha', desc: 'Con leche y perlas', price: '₡2.800', img: 'pc_27', pos: '70% 55%' },
  { cat: 'Mangonadas', name: 'Mangonada mediana', desc: 'Mango, chamoy y tajín', price: '₡2.500', img: 'pc_28', pos: '50% 55%' },
  { cat: 'Mangonadas', name: 'Mangonada grande', desc: 'Mango, chamoy y tajín', price: '₡3.500', img: 'pc_15', pos: '50% 60%' },
  { cat: 'Mangonadas', name: 'Mangonada especial', desc: 'Con fruta fresca y tamarindo', price: '₡4.000', img: 'pc_07', pos: '50% 45%' },
  { cat: 'Frappés y Milkshakes', name: 'Frappé de café', desc: 'Con crema batida', price: '₡2.800', img: 'pc_26', pos: '50% 50%' },
  { cat: 'Frappés y Milkshakes', name: 'Frappé Nutella', desc: 'Con crema y chocolate', price: '₡3.000', img: 'pc_31', pos: '50% 55%' },
  { cat: 'Frappés y Milkshakes', name: 'Milkshake Oreo', desc: 'Cremoso, con galleta', price: '₡2.500', img: 'pc_30', pos: '65% 55%' },
  { cat: 'Frappés y Milkshakes', name: 'Milkshake algodón', desc: 'Dulce y colorido', price: '₡2.500', img: 'pc_30', pos: '35% 55%' },
  { cat: 'Café', name: 'Café negro', desc: 'Frío o caliente', price: '₡1.000', img: 'pc_21', pos: '50% 50%' },
  { cat: 'Café', name: 'Café con leche', desc: 'Frío o caliente', price: '₡1.300', img: 'pc_21', pos: '50% 50%' },
  { cat: 'Café', name: 'Capuchino', desc: 'Vainilla o caramelo', price: '₡1.800', img: 'pc_21', pos: '50% 50%' },
  { cat: 'Café', name: 'Chocolate caliente', desc: 'Con crema batida', price: '₡1.800', img: 'pc_21', pos: '50% 50%' },
  { cat: 'Café', name: 'Frozen Chai', desc: 'Latte helado', price: '₡2.200', img: 'pc_21', pos: '50% 50%' },
  { cat: 'Postres', name: 'Cheesecake de Oreo', desc: 'Porción individual', price: '₡2.200', img: 'pc_17', pos: '50% 50%' },
  { cat: 'Postres', name: 'Ensalada de frutas', desc: 'Con crema y granola', price: '₡2.800', img: 'pc_16', pos: '50% 60%' },
  { cat: 'Postres', name: 'Bingsu', desc: 'Hielo raspado coreano', price: '₡3.500', img: 'pc_34', pos: '50% 50%' },
  { cat: 'Postres', name: 'Crepes dulces', desc: 'Nutella, fresa o banano', price: '₡2.500', img: 'pc_20', pos: '50% 45%' },
  { cat: 'Salado', name: 'Chapatazo', desc: 'Pollo, jamón o mixto', price: '₡3.500', img: 'pc_23', pos: '50% 50%' },
  { cat: 'Salado', name: 'Dim sum', desc: '6 unidades al vapor', price: '₡3.000', img: 'pc_23', pos: '50% 50%' },
];

/* Lo que dice el panda en cada sección (mismo orden que SECCIONES). */
const SECCIONES = ['inicio', 'menu', 'promos', 'fresas', 'tiktok', 'ubicacion'];
const DICHOS = ['¡Vení y date el gusto!', '¿Ya viste el menú?', '2x1 en fresas…', 'Mirá cómo se arma', '+152K en TikTok', '¡Te esperamos en El Roble!'];
const PANDA_FELIZ = new Set(['fresas', 'ubicacion']);

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const conParallax = window.matchMedia('(min-width: 768px)');
const escritorio = window.matchMedia('(min-width: 860px)');

const clamp01 = (n) => Math.min(1, Math.max(0, n));

/* ---------- Menú con filtro ---------- */

function initMenu() {
  const grid = document.getElementById('menu-grid');
  const filtros = document.getElementById('menu-filtros');
  const estado = document.getElementById('menu-estado');
  const tpl = document.getElementById('tpl-card');

  const tarjetas = MENU.map((item) => {
    const card = tpl.content.firstElementChild.cloneNode(true);
    card.dataset.cat = item.cat;
    const img = card.querySelector('img');
    img.style.objectPosition = item.pos;
    img.src = `img/${item.img}.webp`; // loading="lazy" ya viene del template
    card.querySelector('.card__name').textContent = item.name;
    card.querySelector('.card__desc').textContent = item.desc;
    card.querySelector('.card__price').textContent = item.price;
    return card;
  });
  grid.append(...tarjetas);

  const categorias = ['Todo', ...new Set(MENU.map((m) => m.cat))];
  const botones = categorias.map((cat) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'filter';
    b.textContent = cat;
    b.setAttribute('aria-pressed', String(cat === 'Todo'));
    b.addEventListener('click', () => filtrar(cat));
    return b;
  });
  filtros.append(...botones);

  function filtrar(cat) {
    let visibles = 0;
    tarjetas.forEach((card) => {
      const ver = cat === 'Todo' || card.dataset.cat === cat;
      card.hidden = !ver;
      if (ver) visibles += 1;
    });
    botones.forEach((b) => b.setAttribute('aria-pressed', String(b.textContent === cat)));
    estado.textContent = cat === 'Todo'
      ? `Mostrando todo el menú: ${visibles} productos`
      : `Mostrando ${visibles} productos de ${cat}`;
  }
}

/* ---------- Menú móvil (<dialog>) ---------- */

function initDrawer() {
  const drawer = document.getElementById('menu-movil');
  const burger = document.querySelector('.nav__burger');

  burger.addEventListener('click', () => {
    drawer.showModal();
    burger.setAttribute('aria-expanded', 'true');
  });
  // Tocar cualquier parte cierra; si fue un enlace, la navegación sigue su curso.
  drawer.addEventListener('click', () => drawer.close());
  drawer.addEventListener('close', () => burger.setAttribute('aria-expanded', 'false'));
  escritorio.addEventListener('change', (e) => {
    if (e.matches && drawer.open) drawer.close();
  });
}

/* ---------- Carrusel de promos ---------- */

function initPromos() {
  const track = document.getElementById('promos-track');
  document.querySelectorAll('.arrow').forEach((btn) => {
    btn.addEventListener('click', () => {
      track.scrollBy({
        left: Number(btn.dataset.dir) * Math.min(track.clientWidth * 0.85, 396),
        behavior: reduceMotion.matches ? 'auto' : 'smooth',
      });
    });
  });
}

/* ---------- Scroll: parallax, vaso de fresas y panda ----------
   Un solo pase por frame (rAF): primero se leen todas las medidas, después
   se escribe. Nada se escribe si el valor no cambió lo suficiente. */

function initScroll() {
  const hero = document.getElementById('inicio');
  const fresas = document.getElementById('fresas');
  const panda = document.querySelector('.panda');
  const burbuja = document.querySelector('.panda__bubble');
  const secciones = SECCIONES.map((id) => document.getElementById(id));

  let pendiente = false;
  let ultimaSeccion = -1;
  let ultimoP = -1;
  let ultimoY = -1;

  const pedirFrame = () => {
    if (pendiente) return;
    pendiente = true;
    requestAnimationFrame(frame);
  };

  function escribirVaso(p) {
    const tramo = (a, b) => clamp01((p - a) / (b - a)).toFixed(3);
    fresas.style.setProperty('--s1', tramo(0.05, 0.4));
    fresas.style.setProperty('--s2', tramo(0.35, 0.7));
    fresas.style.setProperty('--s3', tramo(0.6, 0.95));
    if (!fresas.classList.contains('is-live')) {
      // Las transiciones se encienden después del primer estado escrito.
      requestAnimationFrame(() => fresas.classList.add('is-live'));
    }
  }

  function frame() {
    pendiente = false;
    const y = window.scrollY;
    const vh = window.innerHeight;
    const rects = secciones.map((s) => s.getBoundingClientRect());

    // Sección activa: la última cuyo borde superior pasó la mitad de la pantalla.
    let sec = 0;
    rects.forEach((r, i) => { if (r.top < vh * 0.5) sec = i; });
    if (sec !== ultimaSeccion) {
      ultimaSeccion = sec;
      panda.classList.toggle('is-happy', PANDA_FELIZ.has(SECCIONES[sec]));
      burbuja.textContent = DICHOS[sec];
    }

    if (reduceMotion.matches) return;

    // Parallax del hero: solo escritorio y solo mientras el hero se ve.
    if (conParallax.matches && rects[0].bottom > 0) {
      hero.style.setProperty('--y', String(Math.round(y)));
    }

    // Progreso del vaso (0-1) según la posición de la sección.
    const r = rects[SECCIONES.indexOf('fresas')];
    const p = clamp01((vh * 0.9 - r.top) / (Math.min(r.height, vh) * 0.9));
    const extremoNuevo = (p === 0 || p === 1) && p !== ultimoP;
    if (Math.abs(p - ultimoP) > 0.003 || extremoNuevo) {
      ultimoP = p;
      escribirVaso(p);
    }

    // Balanceo del panda con el scroll.
    if (y !== ultimoY) {
      ultimoY = y;
      const giro = (Math.sin(y / 180) * 8).toFixed(2);
      const alto = (Math.sin(y / 120) * 6).toFixed(2);
      panda.style.transform = `rotate(${giro}deg) translateY(${alto}px)`;
    }
  }

  // Cambio de preferencias en vivo: volver al estado neutro y recalcular.
  function reiniciar() {
    hero.style.removeProperty('--y');
    ['--s1', '--s2', '--s3'].forEach((v) => fresas.style.removeProperty(v));
    fresas.classList.remove('is-live');
    panda.style.transform = '';
    ultimoP = -1;
    ultimoY = -1;
    pedirFrame();
  }

  window.addEventListener('scroll', pedirFrame, { passive: true });
  window.addEventListener('resize', pedirFrame);
  reduceMotion.addEventListener('change', reiniciar);
  conParallax.addEventListener('change', reiniciar);
  frame();
}

initMenu();
initDrawer();
initPromos();
initScroll();
