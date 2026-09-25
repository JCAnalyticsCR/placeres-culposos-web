/* Pantalla del local — concepto "Póster Bold".
   Rota los afiches solos. Mover el mouse o tocar muestra el panel (qué
   mostrar, anterior/siguiente, pausa, pantalla completa); cada TV recuerda
   su elección en el navegador.
   Parámetros en la URL:
     ?m=promos | fresas | bebidas | postres | todo   qué afiches mostrar
     ?seg=10   segundos por afiche (por defecto 8)
     ?auto     salta la cortina de bienvenida
   Teclas: ← → cambiar afiche · Espacio pausa · F pantalla completa. */

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

// PENDIENTE: horario real del cliente (marcador del diseño: 1 a 9 p. m.).
const HORARIO = { abre: 13, cierra: 21 };
const CLAVE = 'pc-pantalla-vip';

const params = new URLSearchParams(location.search);
const SEG = Math.max(4, Number(params.get('seg')) || 8);

const $ = (id) => document.getElementById(id);
const lienzo = $('lienzo');
const marco = $('marco');
const contAfiches = $('afiches');

let filtro = elegirFiltroInicial();
let lista = [];
let nodos = [];
let i = 0;
let inicio = Date.now();
let pausado = false;

function elegirFiltroInicial() {
  const q = (params.get('m') || '').toLowerCase();
  if (q) return (FILTROS.find((f) => f.id.startsWith(q)) || FILTROS[0]).id;
  try { return JSON.parse(localStorage.getItem(CLAVE) || '{}').filtro || 'todo'; } catch (e) { return 'todo'; }
}

function guardar() {
  try { localStorage.setItem(CLAVE, JSON.stringify({ filtro })); } catch (e) { /* sin almacenamiento */ }
}

/* ---------- Escala: el lienzo de 1920x1080 llena la pantalla ---------- */

function ajustar() {
  const w = innerWidth || document.documentElement.clientWidth || 1920;
  const h = innerHeight || document.documentElement.clientHeight || 1080;
  const s = Math.min(w / 1920, h / 1080);
  lienzo.style.setProperty('--sc', String(Number.isFinite(s) && s > 0 ? s : 1));
}

/* ---------- Afiches ---------- */

function el(tag, clase, texto) {
  const n = document.createElement(tag);
  if (clase) n.className = clase;
  if (texto !== undefined) n.textContent = texto;
  return n;
}

function tamNombre(a) {
  const n = a.name.length;
  if (a.pre) return n > 14 ? 96 : 116;
  return n > 20 ? 118 : n > 12 ? 150 : 190;
}

function crearAfiche(a) {
  const s = el('section', 'afiche');
  const fondo = el('div', 'afiche__fondo');
  const linea = `${a.word} ★ `.repeat(8);
  for (let k = 0; k < 5; k += 1) fondo.append(el('div', '', linea));

  const texto = el('div', 'afiche__texto');
  texto.append(el('div', 'afiche__kicker', a.kicker || 'Promo del mes · Solo en el local'));
  if (a.pre) texto.append(el('div', 'afiche__pre', a.pre));
  const nombre = el('div', 'afiche__nombre', a.name);
  nombre.style.fontSize = `${tamNombre(a)}px`;
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
  contAfiches.textContent = '';
  nodos = lista.map(crearAfiche);
  contAfiches.append(...nodos);
  i = 0;
  mostrar();
  pintarFiltros();
}

function mostrar() {
  nodos.forEach((n, k) => n.classList.toggle('is-on', k === i));
  const a = lista[i];
  $('panda').classList.toggle('is-tea', a.panda === 'tea');
  $('panda-img').src = `img/panda-${a.panda}.webp`;
  $('burbuja').textContent = a.bubble;
  inicio = Date.now();
}

function paso(d) {
  const n = lista.length;
  i = ((i + d) % n + n) % n;
  mostrar();
}

/* ---------- Reloj, estado y progreso ---------- */

function tick() {
  const ahora = new Date();
  const h = ahora.getHours();
  $('hora').textContent = `${h % 12 || 12}:${String(ahora.getMinutes()).padStart(2, '0')}`;
  $('ampm').textContent = h < 12 ? 'a. m.' : 'p. m.';
  const abierto = h >= HORARIO.abre && h < HORARIO.cierra;
  $('estado').textContent = abierto
    ? `Abierto ahora · hasta ${HORARIO.cierra - 12} p. m.`
    : `Hoy abrimos · ${HORARIO.abre - 12} a ${HORARIO.cierra - 12} p. m.`;

  const avance = pausado ? 0 : Math.min(1, (Date.now() - inicio) / (SEG * 1000));
  $('progreso').style.width = `${avance * 100}%`;
  if (!pausado && avance >= 1) paso(1);
}

/* ---------- Panel de control ---------- */

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

function pintarFiltros() {
  const cont = $('filtros');
  cont.textContent = '';
  FILTROS.forEach((f) => {
    const b = el('button', '', f.label);
    b.type = 'button';
    b.setAttribute('aria-pressed', String(f.id === filtro));
    b.addEventListener('click', () => { filtro = f.id; guardar(); armar(); });
    cont.append(b);
  });
}

function alternarPausa() {
  pausado = !pausado;
  inicio = Date.now();
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
    });
  }
}

ajustar();
addEventListener('resize', ajustar);
if ('ResizeObserver' in window) new ResizeObserver(ajustar).observe(document.documentElement);
armar();
initControles();
tick();
setInterval(tick, 250);
marco.classList.add('is-dormido');
