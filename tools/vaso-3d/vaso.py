"""Vaso de fresas con crema en 3D (Blender / Cycles).

Arma la escena completa por código y renderiza la secuencia de cuadros que
la sección #fresas reproduce con el scroll:

    1. Fresas   (cuadros   0-90)  mitades de fresa caen y se apilan en el vaso
    2. Crema    (cuadros  90-165) la crema llena el vaso y se forma el copete
    3. Leche    (cuadros 163-240) hilos de leche condensada y la fresa de arriba

Las posiciones finales de las fresas salen de una simulación de cuerpos
rígidos (Bullet) con semilla fija, así que cada corrida da el mismo vaso.

Uso (Blender 4.2 o 5.x, cualquiera de las dos formas):

    blender -b -P tools/vaso-3d/vaso.py -- --out <carpeta>
    python tools/vaso-3d/vaso.py --out <carpeta>        # con `pip install bpy==4.2.0`

Opciones:
    --out DIR       carpeta de salida para los PNG (obligatoria)
    --step N        renderiza 1 de cada N cuadros (por defecto 4 -> 61 cuadros)
    --frames A,B,C  renderiza solo esos cuadros (pruebas)
    --samples N     muestras de Cycles (por defecto 64, con denoise)
    --scale PCT     porcentaje de la resolución 800x1000 (pruebas: 50)
    --blend FILE    además guarda la escena .blend para abrirla en Blender
    --no-render     solo arma la escena (útil con --blend)

Después, `python tools/vaso-3d/exportar.py <carpeta>` convierte los PNG en
los WebP de img/vaso/.

Unidades: 1 unidad de Blender = 1 dm (el vaso mide 1,15 = 11,5 cm). Bullet
se comporta mejor con piezas de este tamaño que con metros.
"""

import argparse
import json
import math
import os
import random
import sys

import bpy  # primero: con bpy como módulo de pip, bmesh existe solo después
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

# ---------------------------------------------------------------- parámetros

SEMILLA = 7

# Vaso PET transparente (en dm).
ALTO = 1.15
R_BASE = 0.34
R_BOCA = 0.46
PARED = 0.012

# Línea de tiempo (cuadros de escena).
F_FIN = 240
F_FRESAS = (6, 88)       # aterrizaje de la primera y de la última mitad
F_CAIDA = 11             # cuadros que tarda cada mitad en caer
F_CREMA = (90, 126)      # la crema sube dentro del vaso
F_COPETE = (120, 166)    # copete de crema batida, de abajo hacia arriba
F_HILOS = (163, 204)     # leche condensada sobre el copete
F_ADORNO = (204, 214)    # dos mitades sobre el copete
F_CORONA = (212, 226)    # fresa entera arriba

N_MITADES = 22
NIVEL_CREMA = 1.06

RES = (800, 1000)
# Color: "Standard" deja los rojos de la fresa saturados (AgX y Filmic los
# llevan a rosado pastel); la luz está calibrada para no quemar la crema.
LUZ = 0.12         # multiplicador global de las luces
EXPOSICION = 0.0
VISTA = "Standard"

# Reposo de las fresas: la simulación tarda unos minutos, así que su
# resultado se guarda al lado del script y se reutiliza (--resimular lo rehace).
REPOSO_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reposo.json")


def r_int(z):
    """Radio interior del vaso a la altura z."""
    return R_BASE + (R_BOCA - R_BASE) * z / ALTO - PARED


def r_ext(z):
    return R_BASE + (R_BOCA - R_BASE) * z / ALTO


# ---------------------------------------------------------------- utilidades


def args_cli():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--step", type=int, default=4)
    p.add_argument("--frames", default="")
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--scale", type=int, default=100)
    p.add_argument("--blend", default="")
    p.add_argument("--no-render", action="store_true")
    p.add_argument("--resimular", action="store_true")
    p.add_argument("--exposicion", type=float, default=None)
    p.add_argument("--luz", type=float, default=None)
    p.add_argument("--vista", default=None)
    return p.parse_args(argv)


def nuevo_obj(nombre, datos, coleccion=None):
    obj = bpy.data.objects.new(nombre, datos)
    (coleccion or bpy.context.scene.collection).objects.link(obj)
    return obj


def mesh_de_bmesh(nombre, bm):
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    return me


def suave(me, angulo=35):
    """Sombreado suave con bordes vivos por ángulo (Edge Split no hace falta)."""
    for p in me.polygons:
        p.use_smooth = True
    # Blender 4.1+: el auto smooth es por atributo de borde "sharp_edge".
    bm = bmesh.new()
    bm.from_mesh(me)
    lim = math.radians(angulo)
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > lim:
            e.smooth = False
    bm.to_mesh(me)
    bm.free()


def nodo(nt, tipo, x=0, y=0, **props):
    n = nt.nodes.new(tipo)
    n.location = (x, y)
    for k, v in props.items():
        setattr(n, k, v)
    return n


def principled(nombre):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    return mat, nt, bsdf


def set_in(bsdf, **vals):
    nombres = {
        "color": "Base Color", "rough": "Roughness", "ior": "IOR",
        "sss": "Subsurface Weight", "sss_r": "Subsurface Radius", "sss_s": "Subsurface Scale",
        "coat": "Coat Weight", "coat_r": "Coat Roughness", "trans": "Transmission Weight",
        "spec": "Specular IOR Level", "alpha": "Alpha",
    }
    for k, v in vals.items():
        bsdf.inputs[nombres[k]].default_value = v


def rampa(nt, puntos, x=0, y=0):
    r = nodo(nt, "ShaderNodeValToRGB", x, y)
    els = r.color_ramp.elements
    els.remove(els[1])
    els[0].position, els[0].color = puntos[0][0], (*puntos[0][1], 1.0)
    for pos, col in puntos[1:]:
        els.new(pos).color = (*col, 1.0)
    return r


def mezcla(nt, x, y, b_color):
    """Nodo Mix en modo color. Sus entradas se piden por índice: los nombres
    A/B se repiten para float, vector y color."""
    n = nodo(nt, "ShaderNodeMix", x, y, data_type="RGBA")
    n.inputs[7].default_value = (*b_color, 1)
    return n, n.inputs[0], n.inputs[6], n.outputs[2]


# ---------------------------------------------------------------- materiales


def mat_vaso():
    mat, nt, b = principled("PET")
    set_in(b, color=(1, 1, 1, 1), rough=0.03, ior=1.5, trans=1.0, spec=0.6)
    return mat


def mat_piel():
    """Piel de fresa: rojo con variación, semillas (Voronoi) hundidas y brillo húmedo."""
    mat, nt, b = principled("FresaPiel")
    set_in(b, rough=0.3, sss=0.1, sss_r=(1.0, 0.18, 0.1), sss_s=0.03,
           coat=0.2, coat_r=0.08, spec=0.55)
    L = nt.links
    tc = nodo(nt, "ShaderNodeTexCoord", -1400, 200)
    info = nodo(nt, "ShaderNodeObjectInfo", -1400, -300)
    vor = nodo(nt, "ShaderNodeTexVoronoi", -1100, 200)
    vor.inputs["Scale"].default_value = 26.0
    vor.inputs["Randomness"].default_value = 0.8
    L.new(tc.outputs["Object"], vor.inputs["Vector"])

    # Semillas: amarillas en el centro de cada celda, hoyuelo alrededor.
    semilla = nodo(nt, "ShaderNodeMapRange", -850, 300)
    semilla.inputs["From Min"].default_value = 0.07
    semilla.inputs["From Max"].default_value = 0.13
    semilla.inputs["To Min"].default_value = 1.0
    semilla.inputs["To Max"].default_value = 0.0
    L.new(vor.outputs["Distance"], semilla.inputs["Value"])

    hoyo = nodo(nt, "ShaderNodeMapRange", -850, 0)
    hoyo.inputs["From Min"].default_value = 0.06
    hoyo.inputs["From Max"].default_value = 0.34
    L.new(vor.outputs["Distance"], hoyo.inputs["Value"])

    # Rojo base con manchas y hombro más claro cerca del cáliz (atributo t).
    ruido = nodo(nt, "ShaderNodeTexNoise", -1100, -100)
    ruido.inputs["Scale"].default_value = 6.0
    L.new(tc.outputs["Object"], ruido.inputs["Vector"])
    attr_t = nodo(nt, "ShaderNodeAttribute", -1100, -400, attribute_name="t")
    hombro = nodo(nt, "ShaderNodeMapRange", -850, -400)
    hombro.inputs["From Min"].default_value = 0.82
    hombro.inputs["From Max"].default_value = 0.99
    L.new(attr_t.outputs["Fac"], hombro.inputs["Value"])

    rojo = rampa(nt, [(0.3, (0.36, 0.006, 0.012)), (0.7, (0.62, 0.02, 0.03))], -600, -100)
    L.new(ruido.outputs["Fac"], rojo.inputs["Fac"])
    # Variación por pieza: unas más maduras que otras.
    var = nodo(nt, "ShaderNodeHueSaturation", -350, -100)
    rnd = nodo(nt, "ShaderNodeMapRange", -600, -350)
    rnd.inputs["To Min"].default_value = 0.8
    rnd.inputs["To Max"].default_value = 1.15
    L.new(info.outputs["Random"], rnd.inputs["Value"])
    L.new(rnd.outputs["Result"], var.inputs["Value"])
    L.new(rojo.outputs["Color"], var.inputs["Color"])

    _, c_fac, c_a, c_out = mezcla(nt, -150, -100, (0.85, 0.32, 0.22))
    L.new(hombro.outputs["Result"], c_fac)
    L.new(var.outputs["Color"], c_a)

    _, m_fac, m_a, m_out = mezcla(nt, 100, 100, (0.78, 0.55, 0.12))
    L.new(semilla.outputs["Result"], m_fac)
    L.new(c_out, m_a)
    L.new(m_out, b.inputs["Base Color"])

    alt = nodo(nt, "ShaderNodeMath", -500, 200, operation="SUBTRACT")
    L.new(hoyo.outputs["Result"], alt.inputs[0])
    esc = nodo(nt, "ShaderNodeMath", -350, 350, operation="MULTIPLY")
    esc.inputs[1].default_value = -0.6
    L.new(semilla.outputs["Result"], esc.inputs[0])
    L.new(esc.outputs["Value"], alt.inputs[1])
    bump = nodo(nt, "ShaderNodeBump", 100, -300)
    bump.inputs["Strength"].default_value = 0.55
    bump.inputs["Distance"].default_value = 0.004
    L.new(alt.outputs["Value"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return mat


def mat_carne():
    """Cara del corte: borde rojo, pulpa rosada y corazón blanco (atributo carne)."""
    mat, nt, b = principled("FresaCarne")
    set_in(b, rough=0.22, sss=0.5, sss_r=(1.0, 0.35, 0.3), sss_s=0.02,
           coat=0.5, coat_r=0.05, spec=0.6)
    L = nt.links
    attr = nodo(nt, "ShaderNodeAttribute", -900, 0, attribute_name="carne")
    tc = nodo(nt, "ShaderNodeTexCoord", -1200, -300)
    mapeo = nodo(nt, "ShaderNodeMapping", -1000, -300)
    mapeo.inputs["Scale"].default_value = (1.0, 7.0, 1.6)
    L.new(tc.outputs["Object"], mapeo.inputs["Vector"])
    ruido = nodo(nt, "ShaderNodeTexNoise", -800, -300)
    ruido.inputs["Scale"].default_value = 9.0
    ruido.inputs["Detail"].default_value = 6.0
    L.new(mapeo.outputs["Vector"], ruido.inputs["Vector"])
    vetas = nodo(nt, "ShaderNodeMapRange", -600, -300)
    vetas.inputs["To Min"].default_value = -0.12
    vetas.inputs["To Max"].default_value = 0.12
    L.new(ruido.outputs["Fac"], vetas.inputs["Value"])
    suma = nodo(nt, "ShaderNodeMath", -450, 0, operation="ADD", use_clamp=True)
    L.new(attr.outputs["Fac"], suma.inputs[0])
    L.new(vetas.outputs["Result"], suma.inputs[1])
    r = rampa(nt, [
        (0.00, (0.94, 0.72, 0.66)),
        (0.22, (0.90, 0.40, 0.36)),
        (0.48, (0.74, 0.07, 0.07)),
        (0.85, (0.55, 0.02, 0.03)),
        (1.00, (0.40, 0.01, 0.02)),
    ], -250, 0)
    L.new(suma.outputs["Value"], r.inputs["Fac"])
    L.new(r.outputs["Color"], b.inputs["Base Color"])
    bump = nodo(nt, "ShaderNodeBump", -250, -350)
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.003
    L.new(ruido.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return mat


def mat_hoja():
    mat, nt, b = principled("Caliz")
    set_in(b, rough=0.45, sss=0.25, sss_r=(0.3, 1.0, 0.2), sss_s=0.01, spec=0.5)
    L = nt.links
    tc = nodo(nt, "ShaderNodeTexCoord", -700, 0)
    ruido = nodo(nt, "ShaderNodeTexNoise", -500, 0)
    ruido.inputs["Scale"].default_value = 30.0
    L.new(tc.outputs["Object"], ruido.inputs["Vector"])
    r = rampa(nt, [(0.35, (0.04, 0.16, 0.02)), (0.7, (0.12, 0.34, 0.05))], -300, 0)
    L.new(ruido.outputs["Fac"], r.inputs["Fac"])
    L.new(r.outputs["Color"], b.inputs["Base Color"])
    return mat


def mat_crema(nombre, color, rough, escala, bump_f=0.0):
    mat, nt, b = principled(nombre)
    set_in(b, color=(*color, 1), rough=rough, sss=1.0, sss_r=(1.0, 0.9, 0.75),
           sss_s=escala, spec=0.5, coat=0.15, coat_r=0.2)
    if bump_f:
        L = nt.links
        tc = nodo(nt, "ShaderNodeTexCoord", -700, -300)
        ruido = nodo(nt, "ShaderNodeTexNoise", -500, -300)
        ruido.inputs["Scale"].default_value = 18.0
        ruido.inputs["Detail"].default_value = 4.0
        L.new(tc.outputs["Object"], ruido.inputs["Vector"])
        bump = nodo(nt, "ShaderNodeBump", -250, -300)
        bump.inputs["Strength"].default_value = bump_f
        bump.inputs["Distance"].default_value = 0.01
        L.new(ruido.outputs["Fac"], bump.inputs["Height"])
        L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return mat


def mat_leche():
    mat, nt, b = principled("LecheCondensada")
    set_in(b, color=(0.90, 0.70, 0.36, 1), rough=0.06, sss=0.7,
           sss_r=(1.0, 0.75, 0.35), sss_s=0.02, coat=0.6, coat_r=0.03, spec=0.7,
           trans=0.15, ior=1.47)
    return mat


def mat_sticker(ruta_logo):
    mat, nt, b = principled("Sticker")
    set_in(b, rough=0.35, coat=0.4, coat_r=0.12, spec=0.5)
    L = nt.links
    tex = nodo(nt, "ShaderNodeTexImage", -600, 100, interpolation="Cubic")
    tex.image = bpy.data.images.load(ruta_logo)
    L.new(tex.outputs["Color"], b.inputs["Base Color"])
    L.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    mat.blend_method = "HASHED"
    return mat


# ---------------------------------------------------------------- geometría


def perfil_fresa(largo, ancho):
    """Perfil (r, z) de una fresa, de la punta (t=0) al cáliz (t=1)."""
    def f(t):
        if t <= 0.8:
            a = 0.03 + 0.97 * (t / 0.8)
            r = math.sin(math.pi / 2 * a) ** 0.95
            z = 0.84 * (t / 0.8)
        else:
            u = (t - 0.8) / 0.2
            r = math.cos(math.pi / 2 * u) ** 0.45
            z = 0.84 + 0.16 * math.sin(math.pi / 2 * u)
        return r * ancho / 2, (z - 0.5) * largo
    return f


def interp(x, xs, ys):
    if x <= xs[0]:
        return ys[0]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            k = (x - xs[i - 1]) / (xs[i] - xs[i - 1] or 1)
            return ys[i - 1] + k * (ys[i] - ys[i - 1])
    return ys[-1]


def fresa_bm(largo, ancho, rnd, mitad=False, n_t=30, n_phi=36):
    """Fresa entera o partida a lo largo, con atributos t y carne por vértice."""
    f = perfil_fresa(largo, ancho)
    fase = [rnd.uniform(0, 6.28) for _ in range(3)]
    ts = [i / n_t for i in range(n_t + 1)]
    perfil = [f(t) for t in ts]
    zs = [p[1] for p in perfil]
    rs = [p[0] for p in perfil]

    bm = bmesh.new()
    anillos = []
    for i, t in enumerate(ts[1:-1], start=1):
        r, z = perfil[i]
        anillo = []
        for j in range(n_phi):
            phi = 2 * math.pi * j / n_phi
            k = 1 + 0.045 * math.sin(3 * phi + fase[0]) + 0.03 * math.sin(5 * phi + fase[1]) * t
            x = r * k * math.cos(phi) + 0.02 * ancho * math.sin(fase[2]) * (1 - t)
            anillo.append(bm.verts.new((x, r * k * math.sin(phi), z)))
        anillos.append(anillo)
    punta = bm.verts.new((0, 0, zs[0]))
    tope = bm.verts.new((0, 0, zs[-1] - 0.012 * largo))
    for a, b in zip(anillos, anillos[1:]):
        for j in range(n_phi):
            bm.faces.new((a[j], a[(j + 1) % n_phi], b[(j + 1) % n_phi], b[j]))
    for j in range(n_phi):
        bm.faces.new((punta, anillos[0][(j + 1) % n_phi], anillos[0][j]))
        bm.faces.new((tope, anillos[-1][j], anillos[-1][(j + 1) % n_phi]))

    cara_corte = set()
    if mitad:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(1, 0, 0),
                               clear_outer=True, dist=1e-6)
        # Bucle de borde ordenado.
        borde = [e for e in bm.edges if len(e.link_faces) == 1]
        vecinos = {}
        for e in borde:
            a, b = e.verts
            vecinos.setdefault(a, []).append(b)
            vecinos.setdefault(b, []).append(a)
        inicio = borde[0].verts[0]
        bucle, prev, act = [inicio], None, inicio
        while True:
            sig = [v for v in vecinos[act] if v is not prev]
            if not sig or sig[0] is inicio:
                break
            prev, act = act, sig[0]
            bucle.append(act)
        # La cara del corte mira a +x: orientar el bucle en consecuencia.
        centro = Vector((0, 0, sum(v.co.z for v in bucle) / len(bucle)))
        n = Vector((0, 0, 0))
        for i in range(len(bucle)):
            n += (bucle[i].co - centro).cross(bucle[(i + 1) % len(bucle)].co - centro)
        if n.x < 0:
            bucle.reverse()
        # Anillos concéntricos hacia el centro (escalado: nunca se cruzan en la punta).
        previo = bucle
        for s in (0.86, 0.62, 0.36):
            nuevo = [bm.verts.new(centro + (v.co - centro) * s) for v in bucle]
            for i in range(len(bucle)):
                c = bm.faces.new((previo[i], previo[(i + 1) % len(bucle)],
                                  nuevo[(i + 1) % len(bucle)], nuevo[i]))
                cara_corte.add(c)
            previo = nuevo
        vc = bm.verts.new(centro)
        for i in range(len(bucle)):
            cara_corte.add(bm.faces.new((previo[i], previo[(i + 1) % len(bucle)], vc)))

    bm.normal_update()
    capa_t = bm.verts.layers.float.new("t")
    capa_c = bm.verts.layers.float.new("carne")
    for v in bm.verts:
        t = interp(v.co.z, zs, ts)
        v[capa_t] = t
        radio = max(interp(v.co.z, zs, rs), 1e-4)
        en_corte = abs(v.co.x) < 1e-5 and any(fc in cara_corte for fc in v.link_faces)
        v[capa_c] = min(1.0, abs(v.co.y) / radio) ** 0.8 if en_corte else 1.0
    for fc in bm.faces:
        fc.material_index = 1 if fc in cara_corte else 0
    return bm


def caliz_bm(largo, ancho, rnd, n=8):
    """Cáliz: sépalos finos que se abren sobre el hombro de la fresa."""
    f = perfil_fresa(largo, ancho)
    ts = [0.8 + 0.2 * i / 20 for i in range(21)]
    rs = [f(t)[0] for t in ts][::-1]
    zs = [f(t)[1] for t in ts][::-1]
    bm = bmesh.new()
    pasos = 7
    for k in range(n):
        a0 = 2 * math.pi * k / n + rnd.uniform(-0.15, 0.15)
        largo_s = ancho * rnd.uniform(0.42, 0.55)
        ancho_s = ancho * 0.12
        filas = []
        for i in range(pasos + 1):
            s = i / pasos
            rho = 0.015 + s * largo_s
            zsup = interp(rho, rs, zs) if rho <= rs[-1] else zs[-1] - (rho - rs[-1]) * 1.2
            z = zsup + 0.012 + 0.05 * s * s * rnd.uniform(0.3, 1.0)
            w = ancho_s * math.sin(math.pi * min(0.05 + s, 1.0)) ** 0.7
            c = Vector((rho * math.cos(a0), rho * math.sin(a0), z))
            lado = Vector((-math.sin(a0), math.cos(a0), 0)) * w
            filas.append((bm.verts.new(c - lado), bm.verts.new(c + lado)))
        for (a1, b1), (a2, b2) in zip(filas, filas[1:]):
            bm.faces.new((a1, b1, b2, a2))
    # Tallito.
    tallo = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.014,
                                  radius2=0.011, depth=0.09)
    for v in tallo["verts"]:
        v.co = Matrix.Rotation(0.35, 3, "X") @ v.co + Vector((0, 0.01, zs[-1] + 0.05))
    return bm


def crear_fresa(nombre, largo, ancho, rnd, mitad, mats, coleccion=None):
    me = mesh_de_bmesh(nombre, fresa_bm(largo, ancho, rnd, mitad))
    suave(me, 50)
    me.materials.append(mats["piel"])
    me.materials.append(mats["carne"])
    obj = nuevo_obj(nombre, me, coleccion)
    if not mitad:
        cm = mesh_de_bmesh(nombre + "_caliz", caliz_bm(largo, ancho, rnd))
        suave(cm, 60)
        cm.materials.append(mats["hoja"])
        c = nuevo_obj(nombre + "_caliz", cm, coleccion)
        sol = c.modifiers.new("grosor", "SOLIDIFY")
        sol.thickness = 0.006
        c.parent = obj
    return obj


def perfil_vaso():
    """Puntos (r, z) del vaso: fondo con pie y pared recta cónica."""
    pts = [(0.0, 0.03), (R_BASE - 0.05, 0.03), (R_BASE - 0.02, 0.012),
           (R_BASE - 0.004, 0.0), (r_ext(0.02), 0.02)]
    for i in range(1, 13):
        z = 0.02 + (ALTO - 0.02) * i / 12
        pts.append((r_ext(z), z))
    return pts


def torno(pts, seg=128):
    bm = bmesh.new()
    anillos = []
    for r, z in pts:
        if r == 0:
            anillos.append([bm.verts.new((0, 0, z))])
            continue
        anillos.append([bm.verts.new((r * math.cos(2 * math.pi * j / seg),
                                      r * math.sin(2 * math.pi * j / seg), z))
                        for j in range(seg)])
    for a, b in zip(anillos, anillos[1:]):
        if len(a) == 1:
            for j in range(seg):
                bm.faces.new((a[0], b[(j + 1) % seg], b[j]))
        else:
            for j in range(seg):
                bm.faces.new((a[j], a[(j + 1) % seg], b[(j + 1) % seg], b[j]))
    bm.normal_update()
    return bm


def crear_vaso(mats):
    me = mesh_de_bmesh("Vaso", torno(perfil_vaso()))
    suave(me, 40)
    me.materials.append(mats["vaso"])
    vaso = nuevo_obj("Vaso", me)
    sol = vaso.modifiers.new("pared", "SOLIDIFY")
    sol.thickness = PARED
    sol.offset = -1
    sol.use_even_offset = True
    # El vaso no proyecta sombra: sin cáusticas, Cycles no deja pasar la luz
    # directa a través del vidrio y todo lo de adentro se vería gris.
    vaso.visible_shadow = False

    # Labio enrollado del borde.
    bpy.ops.mesh.primitive_torus_add(major_radius=R_BOCA - 0.002, minor_radius=0.013,
                                     major_segments=128, minor_segments=16,
                                     location=(0, 0, ALTO + 0.006))
    labio = bpy.context.active_object
    labio.name = "Labio"
    for p in labio.data.polygons:
        p.use_smooth = True
    labio.data.materials.append(mats["vaso"])
    labio.visible_shadow = False

    # Colisionador grueso e invisible: las fresas solo llegan desde adentro,
    # así que engrosar hacia afuera evita que atraviesen la pared delgada.
    col = nuevo_obj("VasoColision", mesh_de_bmesh("VasoColision", torno(
        [(0.0, 0.03), (r_int(0.03), 0.03)] +
        [(r_int(0.03 + (ALTO - 0.03) * i / 8), 0.03 + (ALTO - 0.03) * i / 8) for i in range(1, 9)] +
        [(r_int(ALTO) + 0.3, ALTO)], seg=48)))
    s2 = col.modifiers.new("grueso", "SOLIDIFY")
    s2.thickness = 0.12
    s2.offset = 1
    col.hide_render = True
    col.display_type = "WIRE"
    return vaso, col


def crear_sticker(mat, zc=0.5, diam=0.5, n=28):
    bm = bmesh.new()
    filas = []
    for i in range(n + 1):
        v = i / n
        z = zc + (v - 0.5) * diam
        r = r_ext(z) + 0.0025
        fila = []
        for j in range(n + 1):
            u = j / n
            phi = -math.pi / 2 + (u - 0.5) * diam / r
            fila.append(bm.verts.new((r * math.cos(phi), r * math.sin(phi), z)))
        filas.append(fila)
    uv = bm.loops.layers.uv.new("UVMap")
    for i in range(n):
        for j in range(n):
            vs = (filas[i][j], filas[i][j + 1], filas[i + 1][j + 1], filas[i + 1][j])
            fc = bm.faces.new(vs)
            for lp, (a, b) in zip(fc.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))):
                lp[uv].uv = (a / n, b / n)
    me = mesh_de_bmesh("Sticker", bm)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    return nuevo_obj("Sticker", me)


def crear_crema_liquida(mat):
    """Tronco de cono interior; una shape key sube la superficie de 0 al nivel final.
    Como el radio es lineal en z, interpolar el anillo de arriba lo mantiene
    pegado a la pared en cualquier nivel."""
    z0, z1 = 0.035, NIVEL_CREMA
    hueco = 0.014
    seg = 96
    bm = bmesh.new()
    abajo = [bm.verts.new(((r_int(z0) - hueco) * math.cos(2 * math.pi * j / seg),
                           (r_int(z0) - hueco) * math.sin(2 * math.pi * j / seg), z0))
             for j in range(seg)]
    arriba = [bm.verts.new(((r_int(z0 + 0.004) - hueco) * math.cos(2 * math.pi * j / seg),
                            (r_int(z0 + 0.004) - hueco) * math.sin(2 * math.pi * j / seg), z0 + 0.004))
              for j in range(seg)]
    c_ab = bm.verts.new((0, 0, z0))
    c_ar = bm.verts.new((0, 0, z0 + 0.004))
    for j in range(seg):
        k = (j + 1) % seg
        bm.faces.new((abajo[j], abajo[k], arriba[k], arriba[j]))
        bm.faces.new((c_ab, abajo[k], abajo[j]))
        bm.faces.new((c_ar, arriba[j], arriba[k]))
    me = mesh_de_bmesh("CremaLiquida", bm)
    suave(me, 30)
    me.materials.append(mat)
    obj = nuevo_obj("CremaLiquida", me)
    obj.shape_key_add(name="Basis")
    lleno = obj.shape_key_add(name="Lleno")
    n_ab = seg
    for idx, v in enumerate(lleno.data):
        if idx < n_ab or idx == 2 * seg:
            continue
        x, y, _ = v.co
        ang = math.atan2(y, x)
        r = r_int(z1) - hueco if idx != 2 * seg + 1 else 0
        v.co = (r * math.cos(ang), r * math.sin(ang), z1)
    return obj, lleno


def curva(nombre, pts, radio=0.0, bisel=None, conico=None, mat=None, res=4):
    cu = bpy.data.curves.new(nombre, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = res
    sp = cu.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (*c, 1.0)
    sp.order_u = 4
    sp.use_endpoint_u = True
    if bisel is not None:
        cu.bevel_mode = "OBJECT"
        cu.bevel_object = bisel
    else:
        cu.bevel_depth = radio
        cu.bevel_resolution = 6
    if conico is not None:
        cu.taper_object = conico
        cu.taper_radius_mode = "OVERRIDE"
    cu.use_fill_caps = True
    cu.bevel_factor_mapping_end = "SPLINE"
    if mat:
        cu.materials.append(mat)
    return nuevo_obj(nombre, cu)


def perfil_2d(nombre, pts, ciclico=False):
    cu = bpy.data.curves.new(nombre, "CURVE")
    cu.dimensions = "2D"
    cu.resolution_u = 6
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, (x, y) in zip(sp.points, pts):
        p.co = (x, y, 0, 1)
    sp.use_cyclic_u = ciclico
    obj = nuevo_obj(nombre, cu)
    obj.hide_render = True
    obj.hide_viewport = True
    return obj


# Copete: hélice que se cierra hacia arriba.
COPETE_R0 = 0.36
COPETE_Z0 = 1.14
COPETE_ALTO = 0.64
COPETE_VUELTAS = 3.4
COPETE_TUBO = 0.14


def copete_en(u):
    ang = 2 * math.pi * COPETE_VUELTAS * u + 0.6
    r = COPETE_R0 * (1 - u) ** 0.8 + 0.01
    z = COPETE_Z0 + COPETE_ALTO * u ** 0.85
    return ang, r, z


def conico_copete(u):
    return 1.0 - 0.72 * u ** 2.2


def altura_copete(rho):
    """Altura aproximada de la superficie del copete a la distancia rho del eje."""
    if rho >= COPETE_R0 + COPETE_TUBO:
        return COPETE_Z0 - 0.02
    mejor = COPETE_Z0
    for i in range(400):
        u = i / 399
        _, r, z = copete_en(u)
        tubo = COPETE_TUBO * conico_copete(u)
        if abs(r - rho) < tubo:
            h = z + math.sqrt(max(tubo ** 2 - (r - rho) ** 2, 0)) * 0.92
            mejor = max(mejor, h)
    return mejor


def crear_copete(mat):
    n = 64
    estrella = [((1 + 0.13 * math.cos(8 * 2 * math.pi * i / n)) * COPETE_TUBO * math.cos(2 * math.pi * i / n),
                 (1 + 0.13 * math.cos(8 * 2 * math.pi * i / n)) * COPETE_TUBO * math.sin(2 * math.pi * i / n))
                for i in range(n)]
    bisel = perfil_2d("PerfilManga", estrella, ciclico=True)
    conico = perfil_2d("ConicoCopete", [(i / 20, conico_copete(i / 20)) for i in range(21)])
    pts = []
    for i in range(160):
        u = i / 159
        ang, r, z = copete_en(u)
        pts.append((r * math.cos(ang), r * math.sin(ang), z))
    return curva("Copete", pts, bisel=bisel, conico=conico, mat=mat, res=6)


def crear_hilos(mat, rnd):
    """Zigzag de leche condensada que cae sobre el copete y se acomoda en sus
    crestas. En los extremos pasa el borde del copete y chorrea un poco."""
    pts = []
    n = 520
    pasadas = 9
    giro = math.radians(28)
    for i in range(n):
        s = i / (n - 1)
        x = 0.5 * math.sin(math.pi * pasadas * s - math.pi / 2)
        y = -0.42 + 0.84 * s + 0.03 * math.sin(40 * s)
        x, y = x * math.cos(giro) - y * math.sin(giro), x * math.sin(giro) + y * math.cos(giro)
        rho = math.hypot(x, y)
        if rho > 0.5:
            x, y = x * 0.5 / rho, y * 0.5 / rho
            rho = 0.5
        pts.append((x, y, altura_copete(rho) + 0.006 + rnd.uniform(-0.003, 0.003)))
    # Grosor irregular, como un hilo que cae de la lata.
    conico = perfil_2d("ConicoHilo", [(i / 40, 0.8 + 0.25 * math.sin(i * 1.7) * math.sin(i * 0.45))
                                      for i in range(41)])
    hilos = curva("Hilos", pts, radio=0.017, conico=conico, mat=mat, res=3)
    hilos.data.taper_radius_mode = "MULTIPLY"
    return hilos


# ---------------------------------------------------------------- física


def simular_reposo(mitades):
    """Deja caer las mitades en el vaso y devuelve su matriz de reposo."""
    escena = bpy.context.scene
    bpy.ops.rigidbody.world_add()
    mundo = escena.rigidbody_world
    mundo.substeps_per_frame = 20
    mundo.solver_iterations = 30
    mundo.point_cache.frame_start = 1
    mundo.point_cache.frame_end = 260
    escena.gravity = (0, 0, -30)

    col = bpy.data.objects["VasoColision"]
    with bpy.context.temp_override(object=col, active_object=col, selected_objects=[col]):
        bpy.ops.rigidbody.object_add(type="PASSIVE")
    col.rigid_body.collision_shape = "MESH"
    col.rigid_body.mesh_source = "FINAL"
    col.rigid_body.friction = 0.7
    col.rigid_body.collision_margin = 0.004

    for m in mitades:
        with bpy.context.temp_override(object=m, active_object=m, selected_objects=[m]):
            bpy.ops.rigidbody.object_add(type="ACTIVE")
        rb = m.rigid_body
        rb.collision_shape = "CONVEX_HULL"
        rb.mass = 0.02
        rb.friction = 0.8
        rb.restitution = 0.05
        rb.linear_damping = 0.35
        rb.angular_damping = 0.6
        rb.collision_margin = 0.003

    for f in range(1, 261):
        escena.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    reposo = [m.evaluated_get(dg).matrix_world.copy() for m in mitades]

    for m in mitades:
        with bpy.context.temp_override(object=m, active_object=m, selected_objects=[m]):
            bpy.ops.rigidbody.object_remove()
    with bpy.context.temp_override(object=col, active_object=col, selected_objects=[col]):
        bpy.ops.rigidbody.object_remove()
    bpy.ops.rigidbody.world_remove()
    return reposo


# ---------------------------------------------------------------- animación


def curvas(ad):
    """F-curves de la acción. Blender 5 quitó Action.fcurves: ahora viven en el
    channelbag del slot asignado (acciones con slots, desde 4.4)."""
    if hasattr(ad.action, "fcurves"):
        return ad.action.fcurves
    from bpy_extras import anim_utils
    return anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot).fcurves


def clave(obj, ruta, f, interp_="BEZIER", easing="AUTO", dato=None):
    objetivo = dato or obj
    objetivo.keyframe_insert(ruta, frame=f)
    ad = objetivo.animation_data
    for fc in curvas(ad):
        if fc.data_path == ruta:
            for kp in fc.keyframe_points:
                if abs(kp.co.x - f) < 0.01:
                    kp.interpolation = interp_
                    kp.easing = easing


def visible_desde(obj, f):
    obj.hide_render = True
    obj.keyframe_insert("hide_render", frame=0)
    obj.hide_render = False
    obj.keyframe_insert("hide_render", frame=f)
    for fc in curvas(obj.animation_data):
        if fc.data_path == "hide_render":
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def animar_caida(obj, m_final, f_llega, rnd, dur=F_CAIDA, altura=2.9, giro=1.6):
    loc, rot, _ = m_final.decompose()
    obj.rotation_mode = "QUATERNION"
    inicio = loc + Vector((rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12), 0))
    inicio.z = altura + rnd.uniform(0, 0.3)
    q0 = rot @ Quaternion(Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized(),
                          rnd.uniform(0.6, 1.0) * giro)
    if q0.dot(rot) < 0:
        q0.negate()
    obj.location = inicio
    obj.rotation_quaternion = q0
    clave(obj, "location", f_llega - dur, "QUAD", "EASE_IN")
    clave(obj, "rotation_quaternion", f_llega - dur, "LINEAR")
    obj.location = loc
    obj.rotation_quaternion = rot
    clave(obj, "location", f_llega, "LINEAR")
    clave(obj, "rotation_quaternion", f_llega, "LINEAR")


def animar_factor(obj, f0, f1):
    cu = obj.data
    cu.bevel_factor_end = 0.0
    clave(obj, "bevel_factor_end", f0, "SINE", "EASE_IN_OUT", dato=cu)
    cu.bevel_factor_end = 1.0
    clave(obj, "bevel_factor_end", f1, "SINE", "EASE_IN_OUT", dato=cu)
    visible_desde(obj, f0 + 1)


# ---------------------------------------------------------------- escena


def luz_area(nombre, loc, mirar, tam, potencia, forma="RECTANGLE", tam_y=None, color=(1, 1, 1),
             sombra=True):
    l = bpy.data.lights.new(nombre, "AREA")
    l.shape = forma
    l.size = tam
    if tam_y:
        l.size_y = tam_y
    l.energy = potencia
    l.color = color
    l.use_shadow = sombra
    obj = nuevo_obj(nombre, l)
    obj.location = loc
    d = Vector(mirar) - Vector(loc)
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    obj.visible_camera = False
    return obj


def armar_escena(a):
    global LUZ, EXPOSICION
    LUZ = a.luz if a.luz is not None else LUZ
    EXPOSICION = a.exposicion if a.exposicion is not None else EXPOSICION
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rnd = random.Random(SEMILLA)
    escena = bpy.context.scene
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    mats = {
        "vaso": mat_vaso(),
        "piel": mat_piel(),
        "carne": mat_carne(),
        "hoja": mat_hoja(),
    }
    # Crema con jugo de fresa: rosada y algo translúcida, deja ver la fruta.
    crema = mat_crema("Crema", (0.97, 0.80, 0.80), 0.22, 0.16)
    batida = mat_crema("CremaBatida", (0.97, 0.955, 0.93), 0.5, 0.035, bump_f=0.12)
    leche = mat_leche()
    sticker = mat_sticker(os.path.join(raiz, "img", "logo.webp"))

    crear_vaso(mats)
    crear_sticker(sticker)

    # Mitades de fresa: tamaños variados, soltadas en columna sobre el vaso.
    col_fresas = bpy.data.collections.new("Fresas")
    escena.collection.children.link(col_fresas)
    mitades = []
    for i in range(N_MITADES):
        largo = rnd.uniform(0.36, 0.46)
        ancho = largo * rnd.uniform(0.78, 0.9)
        m = crear_fresa(f"Mitad{i:02d}", largo, ancho, rnd, True, mats, col_fresas)
        m.location = (rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12), 1.4 + i * 0.42)
        m.rotation_euler = Euler((rnd.uniform(0, 6.28), rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)))
        mitades.append(m)
    bpy.context.view_layer.update()
    reposo = None
    if os.path.exists(REPOSO_JSON) and not a.resimular:
        with open(REPOSO_JSON) as fh:
            datos = json.load(fh)
        if datos.get("semilla") == SEMILLA and len(datos["matrices"]) == N_MITADES:
            reposo = [Matrix(m) for m in datos["matrices"]]
    if reposo is None:
        reposo = simular_reposo(mitades)
        with open(REPOSO_JSON, "w") as fh:
            json.dump({"semilla": SEMILLA,
                       "matrices": [[list(fila) for fila in m] for m in reposo]}, fh)

    # Orden de llegada: de abajo hacia arriba, para que nada atraviese lo ya puesto.
    orden = sorted(range(N_MITADES), key=lambda i: reposo[i].translation.z)
    for k, i in enumerate(orden):
        f = round(F_FRESAS[0] + (F_FRESAS[1] - F_FRESAS[0]) * k / (N_MITADES - 1))
        animar_caida(mitades[i], reposo[i], f, rnd)
        z = reposo[i].translation.z
        rho = reposo[i].translation.xy.length
        print(f"  mitad {i:02d}: z={z:.3f} rho={rho:.3f} llega en {f}")
        if z > ALTO + 0.1 or rho > R_BOCA:
            print("    AVISO: esta mitad quedó fuera del vaso")

    # Crema que sube.
    liquida, lleno = crear_crema_liquida(crema)
    lleno.value = 0.0
    lleno.keyframe_insert("value", frame=F_CREMA[0])
    lleno.value = 1.0
    lleno.keyframe_insert("value", frame=F_CREMA[1])
    visible_desde(liquida, F_CREMA[0] + 1)

    copete = crear_copete(batida)
    animar_factor(copete, *F_COPETE)

    hilos = crear_hilos(leche, rnd)
    animar_factor(hilos, *F_HILOS)

    # Adornos: dos mitades apoyadas en el copete, con el corte hacia la cámara.
    # Se clavan con la punta en la crema, inclinadas hacia afuera.
    for k, ang in enumerate((-2.25, -0.75)):
        m = crear_fresa(f"Adorno{k}", 0.40, 0.34, rnd, True, mats)
        rho = 0.3
        afuera = Vector((math.cos(ang), math.sin(ang), 0))
        eje = (Vector((0, 0, 1)) + afuera * 0.75).normalized()      # z local: punta -> cáliz
        corte = Vector((0, -1, 0.25)) + afuera * 0.35                # x local: cara del corte
        corte = (corte - corte.dot(eje) * eje).normalized()
        rot = Matrix((corte, eje.cross(corte), eje)).transposed().to_4x4()
        base = Vector((rho * math.cos(ang), rho * math.sin(ang), altura_copete(rho)))
        mf = Matrix.Translation(base + eje * 0.1) @ rot
        animar_caida(m, mf, F_ADORNO[0] + k * 6, rnd, dur=9, altura=3.0, giro=1.0)

    # Corona: fresa entera con cáliz, parada sobre la punta del copete.
    corona = crear_fresa("Corona", 0.46, 0.40, rnd, False, mats)
    _, _, z_punta = copete_en(1.0)
    mf = Matrix.Translation((0.0, -0.02, z_punta + 0.1)) @ Matrix.Rotation(0.22, 4, "X") \
        @ Matrix.Rotation(-0.15, 4, "Y")
    animar_caida(corona, mf, F_CORONA[1] - 2, rnd, dur=12, altura=3.1, giro=0.7)

    # Piso que solo recibe sombra.
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    piso = bpy.context.active_object
    piso.name = "Piso"
    piso.is_shadow_catcher = True

    # Luces de estudio: caja suave principal, dos tiras para los filos del vaso,
    # relleno frontal y cenital para el copete.
    # Solo la principal y la cenital dejan sombra en el piso; las demás solo iluminan.
    luz_area("Principal", (-4.0, -4.5, 4.2), (0, 0, 0.9), 3.2, LUZ * 2400)
    luz_area("TiraIzq", (-3.0, 1.2, 1.3), (0, 0, 0.9), 0.35, LUZ * 700, tam_y=4.5, sombra=False)
    luz_area("TiraDer", (3.0, 1.4, 1.4), (0, 0, 0.9), 0.35, LUZ * 900, tam_y=4.5, sombra=False)
    luz_area("Relleno", (3.6, -5.2, 1.6), (0, 0, 0.9), 4.0, LUZ * 700, color=(1.0, 0.96, 0.97),
             sombra=False)
    luz_area("Cenital", (0.3, -0.5, 5.5), (0, 0, 1.3), 2.0, LUZ * 600)

    mundo = bpy.data.worlds.new("Estudio")
    mundo.use_nodes = True
    fondo = mundo.node_tree.nodes["Background"]
    fondo.inputs["Color"].default_value = (0.99, 0.89, 0.93, 1)   # --rosa
    fondo.inputs["Strength"].default_value = 0.3
    escena.world = mundo

    cam_d = bpy.data.cameras.new("Camara")
    cam_d.lens = 80
    cam_d.sensor_fit = "VERTICAL"
    cam_d.sensor_height = 24
    cam = nuevo_obj("Camara", cam_d)
    cam.location = (0, -9.4, 2.4)
    mira = Vector((0, 0, 1.16)) - cam.location
    cam.rotation_euler = mira.to_track_quat("-Z", "Y").to_euler()
    escena.camera = cam

    # Render.
    escena.render.engine = "CYCLES"
    cy = escena.cycles
    cy.device = "CPU"
    cy.samples = a.samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.02
    cy.use_denoising = True
    cy.denoiser = "OPENIMAGEDENOISE"
    cy.max_bounces = 16
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 6
    cy.transmission_bounces = 16
    cy.transparent_max_bounces = 16
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.blur_glossy = 0.6
    cy.film_transparent_glass = True
    cy.film_transparent_roughness = 0.12
    escena.render.film_transparent = True
    escena.render.resolution_x, escena.render.resolution_y = RES
    escena.render.resolution_percentage = a.scale
    escena.render.use_motion_blur = True
    escena.render.motion_blur_shutter = 0.45
    escena.render.image_settings.file_format = "PNG"
    escena.render.image_settings.color_mode = "RGBA"
    escena.render.image_settings.color_depth = "8"
    escena.view_settings.view_transform = a.vista or VISTA
    escena.view_settings.exposure = EXPOSICION
    if escena.view_settings.view_transform == "AgX":
        escena.view_settings.look = "AgX - Punchy"
    escena.frame_start = 0
    escena.frame_end = F_FIN


def main():
    a = args_cli()
    os.makedirs(a.out, exist_ok=True)
    armar_escena(a)
    if a.blend:
        # El logo va empacado dentro del .blend para que abra en cualquier equipo.
        for im in bpy.data.images:
            if im.filepath:
                im.pack()
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))
    if a.no_render:
        return
    escena = bpy.context.scene
    cuadros = ([int(x) for x in a.frames.split(",")] if a.frames
               else list(range(0, F_FIN + 1, a.step)))
    for f in cuadros:
        escena.frame_set(f)
        escena.render.filepath = os.path.join(os.path.abspath(a.out), f"f{f:03d}.png")
        bpy.ops.render.render(write_still=True)
        print(f"cuadro {f} listo", flush=True)


if __name__ == "__main__":
    main()
