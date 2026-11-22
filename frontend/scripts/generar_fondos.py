# Genera los fondos de Umbral (imagenes propias, sin derechos de terceros).
# Uso:  python scripts/generar_fondos.py     (necesita: pip install pillow numpy)
# Para usar tus propias fotos basta con reemplazar los .webp de public/fondos
# conservando el nombre del archivo.
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SALIDA = Path(__file__).resolve().parent.parent / "public" / "fondos"
TINTA, LIMA, BRASA, HUESO = (14, 13, 11), (200, 240, 60), (255, 91, 46), (241, 234, 219)


def grano(img, fuerza=14, semilla=7):
    rng = np.random.default_rng(semilla)
    a = np.asarray(img).astype(np.int16)
    a += rng.normal(0, fuerza, a.shape[:2])[..., None].astype(np.int16)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def vineta(img, fuerza=0.75):
    w, h = img.size
    y, x = np.ogrid[:h, :w]
    d = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2)
    m = np.clip(1 - fuerza * d ** 2.2, 0, 1)[..., None]
    return Image.fromarray((np.asarray(img) * m).astype(np.uint8))


def luz(tam, puntos, color, radio):
    capa = Image.new("RGB", tam, (0, 0, 0))
    ImageDraw.Draw(capa).polygon(puntos, fill=color)
    return capa.filter(ImageFilter.GaussianBlur(radio))


def sumar(a, b, k=1.0):
    return Image.fromarray(np.clip(np.asarray(a).astype(np.float32) + np.asarray(b).astype(np.float32) * k, 0, 255).astype(np.uint8))


def pasillo():
    """Un pasillo de noche con una sola puerta entreabierta."""
    W, H = 2000, 1300
    img = Image.new("RGB", (W, H), TINTA)
    d = ImageDraw.Draw(img)
    fx, fy = W * 0.56, H * 0.46                      # punto de fuga
    def p(x, y, z):                                  # proyeccion sencilla: z de 1 (cerca) a 0 (fondo)
        return (fx + (x - fx) * z, fy + (y - fy) * z)
    # paredes, piso y techo con degradado hacia el fondo
    for i in range(60):
        z0, z1 = 1 - i / 60, 1 - (i + 1) / 60
        t = int(34 * z0 ** 1.6)
        d.polygon([p(-200, H + 300, z0), p(W + 200, H + 300, z0), p(W + 200, H + 300, z1), p(-200, H + 300, z1)], fill=(t + 8, t + 6, t + 3))
        d.polygon([p(-200, -300, z0), p(-200, H + 300, z0), p(-200, H + 300, z1), p(-200, -300, z1)], fill=(t + 2, t + 1, t))
        d.polygon([p(W + 200, -300, z0), p(W + 200, H + 300, z0), p(W + 200, H + 300, z1), p(W + 200, -300, z1)], fill=(t + 3, t + 2, t))
        d.polygon([p(-200, -300, z0), p(W + 200, -300, z0), p(W + 200, -300, z1), p(-200, -300, z1)], fill=(t // 2, t // 2, t // 2))
    # puertas cerradas en ambas paredes
    profundidades = [0.92, 0.66, 0.47, 0.34, 0.245, 0.176, 0.127]
    for lado in (-200, W + 200):
        for z in profundidades:
            z2 = z * 0.86
            marco = [p(lado, H * 0.02, z), p(lado, H + 300, z), p(lado, H + 300, z2), p(lado, H * 0.02, z2)]
            tono = int(10 + 26 * z)
            d.polygon(marco, fill=(tono, tono - 1, tono - 3), outline=(tono + 22, tono + 20, tono + 14))
    img = img.filter(ImageFilter.GaussianBlur(1.6))
    # la puerta abierta: tercera de la izquierda
    z, z2 = 0.47, 0.47 * 0.86
    hueco = [p(-200, H * 0.02, z), p(-200, H + 300, z), p(-200, H + 300, z2), p(-200, H * 0.02, z2)]
    img = sumar(img, luz((W, H), hueco, LIMA, 5))
    img = sumar(img, luz((W, H), hueco, LIMA, 70), 0.9)
    piso = [hueco[1], hueco[2], p(W * 0.72, H + 300, z2 * 1.02), p(W * 0.95, H + 300, z * 1.25)]
    img = sumar(img, luz((W, H), piso, LIMA, 34), 0.55)
    img = sumar(img, luz((W, H), piso, LIMA, 140), 0.35)
    # un resplandor calido al fondo
    img = sumar(img, luz((W, H), [(fx - 40, fy - 60), (fx + 40, fy - 60), (fx + 40, fy + 70), (fx - 40, fy + 70)], BRASA, 60), 0.5)
    return grano(vineta(img, 0.7), 11)


def ciudad():
    """Una fachada de noche, fuera de foco: cada ventana encendida es una puerta abierta."""
    W, H = 2000, 1200
    random.seed(243790)
    img = Image.new("RGB", (W, H), TINTA)
    for desenfoque, n, escala in ((26, 150, 1.0), (9, 60, 0.8), (3, 26, 0.7)):
        capa = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(capa)
        for _ in range(n):
            x, y = random.randrange(0, W, 52), random.randrange(0, H, 74)
            w, h = int(30 * escala), int(46 * escala)
            r = random.random()
            color = LIMA if r < 0.2 else BRASA if r < 0.28 else (random.randint(150, 235),) * 2 + (random.randint(110, 170),)
            brillo = random.uniform(0.35, 1)
            d.rectangle([x, y, x + w, y + h], fill=tuple(int(c * brillo) for c in color))
        img = sumar(img, capa.filter(ImageFilter.GaussianBlur(desenfoque)), 0.8)
    return grano(vineta(img, 0.6), 12, 3)


def cerradura():
    """Luz entrando por el ojo de una cerradura."""
    W, H = 1800, 1200
    img = Image.new("RGB", (W, H), TINTA)
    cx, cy = W * 0.68, H * 0.44
    forma = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(forma)
    d.ellipse([cx - 70, cy - 150, cx + 70, cy - 10], fill=LIMA)
    d.polygon([(cx - 34, cy - 50), (cx + 34, cy - 50), (cx + 78, cy + 190), (cx - 78, cy + 190)], fill=LIMA)
    rayos = Image.new("RGB", (W, H), (0, 0, 0))
    dr = ImageDraw.Draw(rayos)
    for ang in np.linspace(2.35, 3.75, 9):
        ancho = 0.035
        dr.polygon([(cx, cy), (cx + 2600 * np.cos(ang - ancho), cy + 2600 * np.sin(ang - ancho)),
                    (cx + 2600 * np.cos(ang + ancho), cy + 2600 * np.sin(ang + ancho))], fill=(70, 86, 20))
    img = sumar(img, rayos.filter(ImageFilter.GaussianBlur(46)), 0.9)
    img = sumar(img, forma.filter(ImageFilter.GaussianBlur(120)), 0.55)
    img = sumar(img, forma.filter(ImageFilter.GaussianBlur(26)), 0.7)
    img = sumar(img, forma.filter(ImageFilter.GaussianBlur(2)), 1)
    return grano(vineta(img, 0.65), 12, 11)


if __name__ == "__main__":
    SALIDA.mkdir(parents=True, exist_ok=True)
    for nombre, funcion, ancho in (("pasillo", pasillo, 1800), ("ciudad", ciudad, 1800), ("cerradura", cerradura, 1600)):
        im = funcion()
        im = im.resize((ancho, int(im.height * ancho / im.width)), Image.LANCZOS)
        im.save(SALIDA / f"{nombre}.webp", quality=78, method=6)
        print("listo", nombre, im.size)
