# Perfil en papel y tinta azul

El README conserva su propia estructura (cabecera y secciones con etiqueta al margen) y toma del portfolio solo el lenguaje visual: papel, una tinta azul, un acento rojo, Archivo para leer e IBM Plex Mono para las etiquetas.

1. Sube `README.md`, `assets/`, `scripts/` y `.github/` a la raíz del repositorio público `Seebaastiaan/Seebaastiaan`.
2. La carpeta `.github` está oculta en Finder. Usa Cmd + Shift + . para verla.
3. En GitHub abre Actions → Refresh contribution skyline → Run workflow.

## Qué hay

- `assets/profile-top.svg` y `assets/profile-rest.svg` — el contenido, como imagen. El texto dentro de ellas no es enlace.
- `assets/row-*.svg` — las filas de Elsewhere. GitHub no permite enlaces dentro de una imagen, así que la página se corta en franjas: cada fila es su propia imagen y `README.md` la envuelve en un enlace. Las franjas se apilan sin separación (por eso el `<p>` de `README.md` va en una sola línea, sin espacios entre etiquetas, y cada imagen lleva `align="top"`).
- `assets/contributions.json` — conteos diarios del calendario público de GitHub.
- `scripts/compose_readme.py` — contenido y maquetación. **Aquí se edita el texto.**
- `scripts/models.py` — los dibujos pequeños junto a cada proyecto y el skyline.
- `scripts/typeset.py` + `scripts/glyphs.json` — la tipografía. GitHub muestra el README como imagen y una imagen no puede cargar fuentes web, así que Archivo e IBM Plex Mono (licencia SIL OFL) están trazadas a contornos. Se ve igual en cualquier navegador.
- `scripts/contribution_skyline.py` — lee el calendario público y actualiza el JSON.
- `scripts/bake_glyphs.py` — herramienta de desarrollo; solo hace falta si necesitas un carácter que no esté trazado (requiere `pip install fonttools`).

## Editar

Cambia el bloque `Content` al inicio de `scripts/compose_readme.py` y ejecuta:

```sh
python3 scripts/compose_readme.py
```

Para actualizar también los datos:

```sh
python3 scripts/contribution_skyline.py Seebaastiaan
python3 scripts/compose_readme.py
```

En Elsewhere, cada entrada de `ELSEWHERE` genera un `row-<slug>.svg` que debe tener su `<a><img></a>` en `README.md`, en el mismo orden. Cada proyecto usa un dibujo de `MODELS` en `scripts/models.py`.

Python 3.10+, biblioteca estándar, compatible con macOS/Linux/Windows.

## Movimiento

Los dibujos de los proyectos se mueven un poco con CSS dentro del SVG (las barras de la matriz y del diario suben y bajan, el vagón recorre la vía) y respetan `prefers-reduced-motion`. Sin animación quedan en una pose fija. Para quitarlo, borra la línea `styles.append(drawing['css'])` en `scripts/compose_readme.py`.

## Actualización diaria

Se incluyen datos reales del calendario público y un workflow diario. El workflow corre a las 09:23 UTC (03:23 en Ciudad de México), sujeto a retrasos y reglas de GitHub Actions: lee el calendario, recompone la imagen y hace commit solo si algo cambió. Usa el token automático del repositorio; no tienes que crear un token personal.

El lector del calendario depende de la estructura pública del HTML de GitHub. Los conteos no son exclusivamente commits ni miden productividad; la racha y el máximo se calculan sobre el periodo mostrado.

El fondo exterior y el espacio entre la imagen y los botones pertenecen a GitHub y siguen el tema del visitante.
