/* Pantalla del local.
   Dos formatos: Horizontal "Póster Bold" (afiches de promos y productos) y
   Vertical "Catálogo" (afiche destacado arriba + menú por categoría abajo,
   para la TV de pie). Rotan solos. Mover el mouse o tocar muestra el panel
   (formato, qué mostrar, anterior/siguiente, pausa, pantalla completa);
   cada TV recuerda sus elecciones en el navegador.
   Parámetros en la URL:
     ?o=h | v | auto   formato (por defecto: el guardado, o automático)
     ?m=promos | fresas | bebidas | postres | todo   qué afiches mostrar
     ?seg=10           segundos por afiche (por defecto 8)
     ?auto             salta la cortina de bienvenida
   Teclas: ← → cambiar afiche · Espacio pausa · F pantalla completa · V formato. */

'use strict';

// PENDIENTE: precios y textos a validar con el cliente (los 2x son de los afiches).
const AFICHES = [
  { promo: true, cat: 'fresas', pre: '2X', name: 'Fresas con crema', sub: 'Tradicionales · por solo', price: '₡4.000', img: 'pc_12', word: 'FRESAS', bubble: '¡2x en fresas!', panda: 'happy' },
  { promo: true, cat: 'bebidas', pre: '2X', name: 'Milkshakes medianos', sub: 'Uno para vos y otro para compartir', price: '₡4.500', img: 'pc_30', word: 'MILKSHAKE', bubble: '¿Uno para cada quien?', panda: 'tea' },
  { promo: true, cat: 'postres', pre: '2X', name: 'Ensalada de frutas', sub: 'Fresca y bien servida · por solo', price: '₡5.000', img: 'pc_16', word: 'FRUTAS', bubble: '¡Fresquita!', panda: 'happy' },
  { promo: true, cat: 'bebidas', pre: '2X', name: 'Bubble tea', sub: 'Para compartir · por solo', price: '₡5.000', img: 'pc_35', word: 'BUBBLE TEA', bubble: '¡Burbujas para dos!', panda: 'tea' },
  { cat: 'fresas', kicker: 'La estrella de la casa', name: 'Fresas con crema', sub: 'Fresas, crema y leche condensada', price: '₡2.000', img: 'pc_14', word: 'FRESAS', bubble: '¡Mi favorita!', panda: 'happy' },
  { cat: 'fresas', kicker: 'Edición especial', name: 'Fresas rosadas con chocolate', sub: 'Crema sabor fresa y crema sabor chocolate', img: 'pc_25', word: 'ROSADAS', bubble: '¡Nueva!', panda: 'happy' },
  { cat: 'fresas', kicker: 'Para el antojo', name: 'Fresas cremosas', sub: 'Con chocolate y fresa fresca', img: 'pc_29-1100', word: 'CREMOSAS', bubble: 'Date el gusto', panda: 'happy' },
  { cat: 'bebidas', kicker: 'Refrescante', name: 'Mangonada', sub: 'Dulce, picosita y bien fría', img: 'pc_28', word: 'MANGONADA', bubble: '¡Con chilito!', panda: 'tea' },
  { cat: 'bebidas', kicker: 'Bien frío', name: 'Frappé', sub: 'Cremoso y con todo encima', img: 'pc_26', word: 'FRAPPÉ', bubble: '¿Uno fresquito?', panda: 'tea' },
  { cat: 'bebidas', kicker: 'Frío o caliente', name: 'Tu café favorito', sub: 'Late Nutella y más en la barra', img: 'pc_31', word: 'CAFÉ', bubble: '¡Cafecito!', panda: 'tea' },
  { cat: 'postres', kicker: 'Recién hechas', name: 'Crepes dulces', sub: 'Visitanos o pedí por PedidosYa', img: 'pc_20', word: 'CREPES', bubble: '¡Qué rico!', panda: 'happy' },
  { cat: 'postres', kicker: 'Para cerrar', name: 'Cheesecake de Oreo', sub: 'Una porción para el antojo', img: 'pc_17', word: 'CHEESECAKE', bubble: '¿Postrecito?', panda: 'happy' },
  { cat: 'salado', kicker: 'Antojo salado', name: 'Chapatazo', sub: 'Visitanos o pedí por PedidosYa', img: 'pc_23', word: 'CHAPATAZO', bubble: '¡Algo saladito!', panda: 'tea' },
];

const FILTROS = [
  { id: 'todo', label: 'Todo', ok: () => true },
  { id: 'promos', label: 'Solo promos', ok: (a) => a.promo },
  { id: 'fresas', label: 'Fresas', ok: (a) => a.cat === 'fresas' },
  { id: 'bebidas', label: 'Bebidas', ok: (a) => a.cat === 'bebidas' },
  { id: 'postres', label: 'Postres y salado', ok: (a) => a.cat === 'postres' || a.cat === 'salado' },
];

const FORMATOS = [
  { id: 'auto', label: 'Automático', nota: 'según la pantalla' },
  { id: 'h', label: 'Horizontal', nota: 'afiches' },
  { id: 'v', label: 'Vertical', nota: 'catálogo · TV de pie' },
];

// PENDIENTE: horario real del cliente (marcador del diseño: 1 a 9 p. m.).
const HORARIO = { abre: 13, cierra: 21 };
const CLAVE = 'pc-pantalla-vip';

const params = new URLSearchParams(location.search);
const SEG = Math.max(4, Number(params.get('seg')) || 8);
// El catálogo cambia de categoría más despacio que los afiches: se lee más.
const SEG_CAT = Math.round(SEG * 1.5);

const $ = (id) => document.getElementById(id);
const $$ = (sel) => document.querySelectorAll(sel);
const lienzo = $('lienzo');
const marco = $('marco');

const guardado = leer();
let filtro = elegirFiltro();
let formato = elegirFormato();
let lista = [];
let nodosH = [];
let nodosV = [];
let i = 0;
let inicio = Date.now();
let pausado = false;

let categorias = [];
let c = 0;
let inicioCat = Date.now();

function leer() {
  try { return JSON.parse(localStorage.getItem(CLAVE) || '{}'); } catch (e) { return {}; }
}
function guardar() {
  try { localStorage.setItem(CLAVE, JSON.stringify({ filtro, formato })); } catch (e) { /* sin almacenamiento */ }
}
function elegirFiltro() {
  const q = (params.get('m') || '').toLowerCase();
  if (q) return (FILTROS.find((f) => f.id.startsWith(q)) || FILTROS[0]).id;
  return guardado.filtro || 'todo';
}
function elegirFormato() {
  const q = (params.get('o') || '').toLowerCase();
  if (FORMATOS.some((f) => f.id === q)) return q;
  return FORMATOS.some((f) => f.id === guardado.formato) ? guardado.formato : 'auto';
}

/* ---------- Formato y escala ---------- */

function esVertical() {
  if (formato === 'v') return true;
  if (formato === 'h') return false;
  return (innerHeight || 1080) > (innerWidth || 1920);
}

function ajustar() {
  const vertical = esVertical();
  lienzo.classList.toggle('is-v', vertical);
  const base = vertical ? [1080, 1920] : [1920, 1080];
  const w = innerWidth || document.documentElement.clientWidth || base[0];
  const h = innerHeight || document.documentElement.clientHeight || base[1];
  const s = Math.min(w / base[0], h / base[1]);
  lienzo.style.setProperty('--sc', String(Number.isFinite(s) && s > 0 ? s : 1));
}

function cambiarFormato(id) {
  formato = id;
  guardar();
  ajustar();
  pintarBotones();
}

/* ---------- Afiches ---------- */

function el(tag, clase, texto) {
  const n = document.createElement(tag);
  if (clase) n.className = clase;
  if (texto !== undefined) n.textContent = texto;
  return n;
}

function tamNombre(a, vertical) {
  const n = a.name.length;
  if (vertical) {
    if (a.pre) return n > 14 ? 64 : 78;
    return n > 20 ? 72 : n > 12 ? 92 : 120;
  }
  if (a.pre) return n > 14 ? 96 : 116;
  return n > 20 ? 110 : n > 12 ? 130 : 170;
}

function crearAfiche(a, vertical) {
  const s = el('section', vertical ? 'vafiche' : 'afiche');
  const fondo = el('div', 'afiche__fondo');
  const linea = `${a.word} ★ `.repeat(8);
  for (let k = 0; k < (vertical ? 4 : 5); k += 1) fondo.append(el('div', '', linea));

  const texto = el('div', 'afiche__texto');
  texto.append(el('div', 'afiche__kicker', a.kicker || 'Promo del mes · Solo en el local'));
  if (a.pre) texto.append(el('div', 'afiche__pre', a.pre));
  const nombre = el('div', 'afiche__nombre', a.name);
  nombre.style.fontSize = `${tamNombre(a, vertical)}px`;
  texto.append(nombre, el('div', 'afiche__sub', a.sub));
  if (a.price) texto.append(el('div', 'afiche__precio', a.price));

  const foto = el('div', 'afiche__foto');
  const borrosa = el('img', 'borroso');
  borrosa.src = `img/${a.img}.webp`;
  borrosa.alt = '';
  const nitida = el('img', 'nitida');
  nitida.src = `img/${a.img}.webp`;
  nitida.alt = a.name;
  foto.append(borrosa, nitida);

  s.append(fondo, texto, foto);
  return s;
}

function armar() {
  const f = FILTROS.find((x) => x.id === filtro) || FILTROS[0];
  lista = AFICHES.filter(f.ok);
  if (!lista.length) lista = AFICHES;
  nodosH = lista.map((a) => crearAfiche(a, false));
  nodosV = lista.map((a) => crearAfiche(a, true));
  $('afiches-h').replaceChildren(...nodosH);
  $('afiches-v').replaceChildren(...nodosV);
  i = 0;
  mostrar();
  pintarBotones();
}

function mostrar() {
  nodosH.forEach((n, k) => n.classList.toggle('is-on', k === i));
  nodosV.forEach((n, k) => n.classList.toggle('is-on', k === i));
  const a = lista[i];
  $$('.js-panda').forEach((p) => p.classList.toggle('is-tea', a.panda === 'tea'));
  $$('.js-panda-img').forEach((img) => { img.src = `img/panda-${a.panda}.webp`; });
  $$('.js-burbuja').forEach((b) => { b.textContent = a.bubble; });
  inicio = Date.now();
}

function paso(d) {
  const n = lista.length;
  i = ((i + d) % n + n) % n;
  mostrar();
}

/* ---------- Catálogo (vertical): el menú de datos.js por categoría ---------- */

function armarCatalogo() {
  const menu = typeof MENU !== 'undefined' ? MENU : [];
  const cats = [...new Set(menu.map((m) => m.cat))];
  categorias = cats.map((cat) => ({ cat, items: menu.filter((m) => m.cat === cat).slice(0, 6) }));
  $('cat-puntos').replaceChildren(...categorias.map(() => el('span')));
  c = 0;
  pintarCategoria();
}

function pintarCategoria() {
  if (!categorias.length) return;
  const { cat, items } = categorias[c];
  $('cat-titulo').textContent = cat;
  $('cat-grid').replaceChildren(...items.map((it) => {
    const card = el('article', 'vitem' + (it.img ? '' : ' sin-foto'));
    const foto = el('div', 'vitem__foto');
    const img = el('img');
    img.alt = '';
    img.decoding = 'async';
    if (it.img) {
      img.src = `img/${it.img}.webp`;
      img.style.objectPosition = it.pos;
    } else {
      img.src = 'img/panda-tea.webp';
    }
    foto.append(img);
    const body = el('div', 'vitem__body');
    body.append(el('div', 'vitem__nombre', it.name), el('div', 'vitem__desc', it.desc), el('div', 'vitem__precio', it.price));
    card.append(foto, body);
    return card;
  }));
  [...$('cat-puntos').children].forEach((p, k) => p.classList.toggle('is-on', k === c));
  inicioCat = Date.now();
}

function siguienteCategoria() {
  const cont = document.querySelector('.vcatalogo');
  cont.classList.add('is-cambio');
  setTimeout(() => {
    c = (c + 1) % categorias.length;
    pintarCategoria();
    cont.classList.remove('is-cambio');
  }, 450);
  inicioCat = Date.now();
}

/* ---------- Reloj, estado y progreso ---------- */

function tick() {
  const ahora = new Date();
  const h = ahora.getHours();
  const hora = `${h % 12 || 12}:${String(ahora.getMinutes()).padStart(2, '0')}`;
  const ap = h < 12 ? 'a. m.' : 'p. m.';
  const abierto = h >= HORARIO.abre && h < HORARIO.cierra;
  const estado = abierto
    ? `Abierto ahora · hasta ${HORARIO.cierra - 12} p. m.`
    : `Hoy abrimos · ${HORARIO.abre - 12} a ${HORARIO.cierra - 12} p. m.`;
  $$('.js-hora').forEach((n) => { n.textContent = hora; });
  $$('.js-ampm').forEach((n) => { n.textContent = ap; });
  $$('.js-estado').forEach((n) => { n.textContent = estado; });

  const avance = pausado ? 0 : Math.min(1, (Date.now() - inicio) / (SEG * 1000));
  $$('.js-progreso').forEach((n) => { n.style.width = `${avance * 100}%`; });
  if (!pausado && avance >= 1) paso(1);
  if (!pausado && lienzo.classList.contains('is-v') && Date.now() - inicioCat >= SEG_CAT * 1000) siguienteCategoria();
}

/* ---------- Panel de control y cortina ---------- */

let dormir = 0;
function despertar() {
  $('panel').classList.add('is-on');
  marco.classList.remove('is-dormido');
  clearTimeout(dormir);
  dormir = setTimeout(() => {
    $('panel').classList.remove('is-on');
    marco.classList.add('is-dormido');
  }, 3500);
}

function boton(texto, activo, alHacerClic, nota) {
  const b = el('button', '', texto);
  b.type = 'button';
  if (nota) b.append(el('small', '', nota));
  b.setAttribute('aria-pressed', String(activo));
  b.addEventListener('click', (e) => { e.stopPropagation(); alHacerClic(); });
  return b;
}

function pintarBotones() {
  $('filtros').replaceChildren(...FILTROS.map((f) => boton(f.label, f.id === filtro, () => { filtro = f.id; guardar(); armar(); })));
  $('formatos').replaceChildren(...FORMATOS.map((f) => boton(f.label, f.id === formato, () => cambiarFormato(f.id))));
  const cf = $('cortina-formatos');
  if (cf) cf.replaceChildren(...FORMATOS.map((f) => boton(f.label, f.id === formato, () => cambiarFormato(f.id), f.nota)));
}

function alternarPausa() {
  pausado = !pausado;
  inicio = Date.now();
  inicioCat = Date.now();
  $('btn-pausa').textContent = pausado ? 'Reanudar' : 'Pausa';
}

function pantallaCompleta() {
  const raiz = document.documentElement;
  if (!document.fullscreenElement) { if (raiz.requestFullscreen) raiz.requestFullscreen().catch(() => {}); }
  else if (document.exitFullscreen) document.exitFullscreen();
}

function initControles() {
  marco.addEventListener('mousemove', despertar);
  marco.addEventListener('click', despertar);
  $('panel').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-accion]');
    if (!b) return;
    const acc = b.dataset.accion;
    if (acc === 'prev') paso(-1);
    else if (acc === 'next') paso(1);
    else if (acc === 'pausa') alternarPausa();
    else if (acc === 'full') pantallaCompleta();
  });
  addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') paso(1);
    else if (e.key === 'ArrowLeft') paso(-1);
    else if (e.key === ' ') { e.preventDefault(); alternarPausa(); }
    else if (e.key === 'f' || e.key === 'F') pantallaCompleta();
    else if (e.key === 'v' || e.key === 'V') {
      const k = FORMATOS.findIndex((f) => f.id === formato);
      cambiarFormato(FORMATOS[(k + 1) % FORMATOS.length].id);
    }
  });

  const cortina = $('cortina');
  if (params.has('auto') || params.has('sinboton')) {
    cortina.remove();
  } else {
    $('btn-iniciar').addEventListener('click', () => {
      pantallaCompleta();
      cortina.classList.add('is-out');
      setTimeout(() => cortina.remove(), 700);
      inicio = Date.now();
      inicioCat = Date.now();
    });
  }
}

ajustar();
addEventListener('resize', ajustar);
if ('ResizeObserver' in window) new ResizeObserver(ajustar).observe(document.documentElement);
armar();
armarCatalogo();
initControles();
tick();
setInterval(tick, 250);
marco.classList.add('is-dormido');
