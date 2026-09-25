/* Pantalla del local: arma las diapositivas con los datos de datos.js y las
   rota sola. Reloj y fecha en vivo, foto de redes que cambia, estado
   abierto/cerrado según el horario, pantalla completa con un toque o F.
   Parámetros en la URL:
     ?v=1        vertical (franja arriba)
     ?seg=10     segundos por diapositiva (por defecto 9)
     ?sinboton   oculta el botón de pantalla completa (para el kiosco) */

'use strict';

const params = new URLSearchParams(location.search);
const SEG = Math.max(4, Number(params.get('seg')) || 9);
// PENDIENTE: horario real del cliente (marcador del diseño: 13:00 a 21:00).
const HORARIO = { abre: 13, cierra: 21 };

if (params.has('v')) document.body.classList.add('tv--vertical');
if (params.has('sinboton')) document.body.classList.add('tv--sin-boton');

const DIAS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];
const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

/* ---------- Reloj y estado ---------- */

function reloj() {
  const ahora = new Date();
  const h = ahora.getHours();
  const hora12 = h % 12 || 12;
  const mm = String(ahora.getMinutes()).padStart(2, '0');
  document.getElementById('hora').textContent = `${hora12}:${mm}`;
  document.getElementById('sufijo').textContent = h < 12 ? 'a. m.' : 'p. m.';
  document.getElementById('fecha').textContent = `${DIAS[ahora.getDay()]} ${ahora.getDate()} de ${MESES[ahora.getMonth()]}`;
  const abierto = h >= HORARIO.abre && h < HORARIO.cierra;
  document.getElementById('estado').classList.toggle('is-cerrado', !abierto);
  document.getElementById('estado-texto').textContent = abierto
    ? `Abierto · hasta las ${HORARIO.cierra - 12} p. m.`
    : `Hoy abrimos · ${HORARIO.abre - 12} a ${HORARIO.cierra - 12} p. m.`;
}

/* ---------- Diapositivas ---------- */

function el(tag, clase, texto) {
  const n = document.createElement(tag);
  if (clase) n.className = clase;
  if (texto !== undefined) n.textContent = texto;
  return n;
}

function slidePromo(p) {
  const s = el('section', 'slide slide--promo');
  const card = el('div', `promo-card promo-card--${p.tono}`);
  card.append(el('span', 'promo-card__chip', 'Promo del mes · solo en el local'));
  card.append(el('div', 'promo-card__big display', p.big));
  card.append(el('div', 'promo-card__name display', p.name));
  card.append(el('div', 'promo-card__note', p.note));
  card.append(el('div', 'promo-card__price', p.price));
  s.append(card);
  return s;
}

function slideMenu(cat, items) {
  const s = el('section', 'slide slide--menu');
  const head = el('div');
  head.append(el('div', 'kicker', 'Nuestro menú · precios en colones'));
  head.append(el('h2', 'display', cat));
  s.append(head);
  const grid = el('div', 'menu-tv');
  items.slice(0, 4).forEach((it) => {
    const card = el('article', 'menu-tv__item' + (it.img ? '' : ' sin-foto'));
    const media = el('div', 'menu-tv__media');
    const img = el('img');
    img.alt = '';
    img.decoding = 'async';
    if (it.img) {
      img.src = `img/${it.img}.webp`;
      img.style.objectPosition = it.pos;
    } else {
      img.src = 'img/panda-tea.webp';
    }
    media.append(img);
    const body = el('div', 'menu-tv__body');
    body.append(el('div', 'menu-tv__name', it.name));
    body.append(el('div', 'menu-tv__desc', it.desc));
    body.append(el('div', 'menu-tv__price', it.price));
    card.append(media, body);
    grid.append(card);
  });
  s.append(grid);
  return s;
}

function slideStar() {
  const s = el('section', 'slide slide--star');
  const copy = el('div');
  copy.append(el('div', 'kicker', 'La estrella de la casa'));
  const h = el('h2', 'display');
  h.append('Fresas', document.createElement('br'), 'con crema');
  copy.append(h);
  copy.append(el('p', '', 'Fresas frescas, crema batida y leche condensada. Así de simple, así de bueno.'));
  copy.append(el('div', 'precio', '₡2.000'));
  const fig = el('figure');
  const img = el('img');
  img.src = 'img/vaso/g/80.webp';
  img.alt = '';
  fig.append(img);
  s.append(copy, fig);
  return s;
}

function slideRedes() {
  const s = el('section', 'slide slide--redes');
  const copy = el('div');
  copy.append(el('div', 'kicker', 'Seguinos y etiquetanos'));
  const h = el('h2', 'display');
  h.append('¿Ya nos', document.createElement('br'));
  h.append(el('span', '', 'seguís?'));
  copy.append(h);
  const pills = el('div', 'pills');
  ['Instagram', 'TikTok', 'Facebook'].forEach((r) => pills.append(el('span', '', r)));
  copy.append(pills);
  copy.append(el('div', 'redes-tv__handle', '@placeresculpososcr'));
  const qr = el('div', 'qr-big');
  const img = el('img');
  img.src = 'img/qr-whatsapp.svg';
  img.alt = 'Código QR para pedir por WhatsApp';
  qr.append(img, el('b', '', 'Pedí por WhatsApp'));
  s.append(copy, qr);
  return s;
}

function armarSlides() {
  const slides = [];
  const cats = [...new Set(MENU.map((m) => m.cat))];
  // Orden: promo, menú, promo, menú… y de vez en cuando la estrella y redes.
  let k = 0;
  cats.forEach((cat, i) => {
    slides.push(slideMenu(cat, MENU.filter((m) => m.cat === cat)));
    if (PROMOS[k]) slides.push(slidePromo(PROMOS[k++]));
    if (i === 1) slides.push(slideStar());
    if (i === 4) slides.push(slideRedes());
  });
  while (PROMOS[k]) slides.push(slidePromo(PROMOS[k++]));
  return slides;
}

function initSlides() {
  const escena = document.getElementById('escena');
  const slides = armarSlides();
  slides.forEach((s) => escena.append(s));
  let i = 0;
  slides[0].classList.add('is-on');
  setInterval(() => {
    const actual = slides[i];
    i = (i + 1) % slides.length;
    actual.classList.remove('is-on');
    actual.classList.add('is-off');
    setTimeout(() => actual.classList.remove('is-off'), 1000);
    slides[i].classList.add('is-on');
  }, SEG * 1000);
}

/* ---------- Foto de redes que rota ---------- */

function initFotos() {
  const img = document.getElementById('foto-red-img');
  const tag = document.getElementById('foto-red-tag');
  let i = 0;
  setInterval(() => {
    i = (i + 1) % FOTOS_REDES.length;
    img.classList.add('is-fading');
    setTimeout(() => {
      img.src = `img/${FOTOS_REDES[i].img}.webp`;
      tag.textContent = FOTOS_REDES[i].red;
      img.onload = () => img.classList.remove('is-fading');
    }, 900);
  }, 6000);
}

/* ---------- Pantalla completa ---------- */

function initFull() {
  const btn = document.getElementById('btn-full');
  const pedir = () => {
    const raiz = document.documentElement;
    if (!document.fullscreenElement && raiz.requestFullscreen) raiz.requestFullscreen().catch(() => {});
  };
  btn.addEventListener('click', pedir);
  document.addEventListener('keydown', (e) => { if (e.key === 'f' || e.key === 'F') pedir(); });
  document.addEventListener('fullscreenchange', () => {
    document.body.classList.toggle('is-full', Boolean(document.fullscreenElement));
  });
  // Al tocar en cualquier parte (TV táctil o mouse) también entra.
  document.getElementById('escena').addEventListener('click', pedir);
}

reloj();
setInterval(reloj, 1000);
initSlides();
initFotos();
initFull();
