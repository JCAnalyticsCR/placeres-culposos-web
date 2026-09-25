/* Placeres Culposos CR — datos compartidos por la landing (app.js) y la
   pantalla del local (pantalla.js). Se carga antes que ambos. */

'use strict';

/* ---------- Datos del menú ----------
   PENDIENTE: validar con el cliente. Solo son reales los precios de los
   afiches (fresas tradicionales ₡2.000 y las promos 2x). `img` es el nombre
   en img/ sin extensión; `pos` es el object-position del recorte. Con
   `img: null` la tarjeta muestra el panda con "Foto pronto": mejor eso que
   repetir la foto de otro producto o mostrar uno equivocado. `ing` son los
   ingredientes que se muestran al pasar el mouse (PENDIENTE: validarlos). */
const MENU = [
  { cat: 'Fresas con crema', name: 'Tradicionales', desc: 'Fresas, crema y leche condensada', price: '₡2.000', img: 'pc_12', pos: '50% 0%', ing: ['Fresas frescas', 'Crema batida', 'Leche condensada'] },
  { cat: 'Fresas con crema', name: 'Con chocolate', desc: 'Crema y chocolate derretido', price: '₡2.500', img: 'pc_14', pos: '50% 50%', ing: ['Fresas frescas', 'Crema batida', 'Chocolate derretido'] },
  // PENDIENTE: no hay foto de Fresas Dubái; pc_22 es el afiche general de fresas.
  { cat: 'Fresas con crema', name: 'Fresas Dubái', desc: 'Pistacho, kunafa y chocolate', price: '₡3.500', img: 'pc_22', pos: '50% 0%', ing: ['Fresas frescas', 'Pistacho', 'Kunafa crocante', 'Chocolate'] },
  { cat: 'Fresas con crema', name: 'Rosadas con chocolate', desc: 'Edición especial', price: '₡3.000', img: 'pc_25', pos: '50% 55%', ing: ['Fresas frescas', 'Crema sabor fresa', 'Chocolate'] },
  { cat: 'Bubble Tea', name: 'Taro', desc: 'Con perlas de tapioca', price: '₡2.500', img: 'pc_27', pos: '50% 55%', ing: ['Té con leche', 'Taro', 'Perlas de tapioca'] },
  { cat: 'Bubble Tea', name: 'Fresa', desc: 'Con perlas de tapioca', price: '₡2.500', img: 'pc_35', pos: '50% 75%', ing: ['Té con leche', 'Fresa', 'Perlas de tapioca'] },
  { cat: 'Bubble Tea', name: 'Mango', desc: 'Con perlas de tapioca', price: '₡2.500', img: null, pos: null, ing: ['Té con leche', 'Mango', 'Perlas de tapioca'] },
  { cat: 'Bubble Tea', name: 'Matcha', desc: 'Con leche y perlas', price: '₡2.800', img: null, pos: null, ing: ['Matcha', 'Leche', 'Perlas de tapioca'] },
  { cat: 'Mangonadas', name: 'Mangonada mediana', desc: 'Mango, chamoy y tajín', price: '₡2.500', img: 'pc_28', pos: '50% 55%', ing: ['Mango', 'Chamoy', 'Tajín', 'Tamarindo'] },
  { cat: 'Mangonadas', name: 'Mangonada grande', desc: 'Mango, chamoy y tajín', price: '₡3.500', img: 'pc_15', pos: '50% 60%', ing: ['Mango', 'Chamoy', 'Tajín', 'Tamarindo'] },
  { cat: 'Mangonadas', name: 'Mangonada especial', desc: 'Con fruta fresca y tamarindo', price: '₡4.000', img: 'pc_07', pos: '50% 45%', ing: ['Mango', 'Fruta fresca', 'Chamoy', 'Tajín', 'Tamarindo'] },
  { cat: 'Frappés y Milkshakes', name: 'Frappé de café', desc: 'Con crema batida', price: '₡2.800', img: 'pc_26', pos: '50% 25%', ing: ['Café', 'Leche', 'Hielo', 'Crema batida'] },
  { cat: 'Frappés y Milkshakes', name: 'Frappé Nutella', desc: 'Con crema y chocolate', price: '₡3.000', img: 'pc_31', pos: '50% 25%', ing: ['Nutella', 'Leche', 'Hielo', 'Crema batida'] },
  { cat: 'Frappés y Milkshakes', name: 'Milkshake Oreo', desc: 'Cremoso, con galleta', price: '₡2.500', img: 'pc_13', pos: '50% 50%', ing: ['Helado', 'Leche', 'Galleta Oreo', 'Crema batida'] },
  { cat: 'Frappés y Milkshakes', name: 'Milkshake algodón', desc: 'Dulce y colorido', price: '₡2.500', img: 'pc_30-algodon', pos: '50% 44%', ing: ['Helado', 'Leche', 'Algodón de azúcar', 'Chispas'] },
  { cat: 'Café', name: 'Café negro', desc: 'Frío o caliente', price: '₡1.000', img: 'pc_21', pos: '50% 50%', ing: ['Café'] },
  { cat: 'Café', name: 'Café con leche', desc: 'Frío o caliente', price: '₡1.300', img: null, pos: null, ing: ['Café', 'Leche'] },
  { cat: 'Café', name: 'Capuchino', desc: 'Vainilla o caramelo', price: '₡1.800', img: null, pos: null, ing: ['Espresso', 'Leche espumada', 'Vainilla o caramelo'] },
  { cat: 'Café', name: 'Chocolate caliente', desc: 'Con crema batida', price: '₡1.800', img: null, pos: null, ing: ['Chocolate', 'Leche', 'Crema batida'] },
  { cat: 'Café', name: 'Frozen Chai', desc: 'Latte helado', price: '₡2.200', img: null, pos: null, ing: ['Chai', 'Leche', 'Hielo'] },
  { cat: 'Postres', name: 'Cheesecake de Oreo', desc: 'Porción individual', price: '₡2.200', img: 'pc_17', pos: '50% 50%', ing: ['Queso crema', 'Galleta Oreo', 'Base de galleta'] },
  { cat: 'Postres', name: 'Ensalada de frutas', desc: 'Con crema y granola', price: '₡2.800', img: 'pc_16', pos: '50% 60%', ing: ['Fruta de temporada', 'Crema', 'Granola'] },
  { cat: 'Postres', name: 'Bingsu', desc: 'Hielo raspado coreano', price: '₡3.500', img: 'pc_34', pos: '50% 75%', ing: ['Hielo raspado', 'Leche condensada', 'Toppings'] },
  { cat: 'Postres', name: 'Crepes dulces', desc: 'Nutella, fresa o banano', price: '₡2.500', img: 'pc_20', pos: '50% 0%', ing: ['Crepe', 'Nutella, fresa o banano', 'Crema batida'] },
  { cat: 'Salado', name: 'Chapatazo', desc: 'Pollo, jamón o mixto', price: '₡3.500', img: 'pc_23', pos: '50% 50%', ing: ['Pan chapata', 'Pollo, jamón o mixto', 'Queso', 'Vegetales'] },
  { cat: 'Salado', name: 'Dim sum', desc: '6 unidades al vapor', price: '₡3.000', img: null, pos: null, ing: ['Masa al vapor', 'Relleno de cerdo o pollo'] },
];

/* Promos del mes: las mismas del carrusel de la landing (index.html); la
   pantalla del local las muestra a tamaño completo. PENDIENTE: validar. */
const PROMOS = [
  { big: '2x', name: 'Fresas con crema', note: 'tradicionales', price: '₡4.000', tono: 'dark' },
  { big: '2x', name: 'Milkshakes medianos', note: 'por solo', price: '₡4.500', tono: 'white' },
  { big: '2x', name: 'Ensalada de frutas', note: 'por solo', price: '₡5.000', tono: 'yellow' },
  { big: '2x', name: 'Bubble Tea', note: 'por solo', price: '₡5.000', tono: 'teal' },
];

/* Fotos de redes para la franja de la pantalla (mismas de "En redes"). */
const FOTOS_REDES = [
  { img: 'pc_31', red: 'Instagram', alt: 'Frappé de Nutella' },
  { img: 'pc_20', red: 'TikTok', alt: 'Crepes dulces' },
  { img: 'pc_23', red: 'Facebook', alt: 'Chapatazo' },
  { img: 'pc_25', red: 'Instagram', alt: 'Fresas rosadas con chocolate' },
  { img: 'pc_35', red: 'TikTok', alt: 'Bubble tea de fresa' },
  { img: 'pc_08', red: 'TikTok', alt: 'Mamá e hijo con fresas con crema' },
];
