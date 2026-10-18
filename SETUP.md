# Perfil crema y negro

1. Sube `README.md`, `assets/`, `scripts/` y `.github/` a la raíz del repositorio público `Seebaastiaan/Seebaastiaan`.
2. La carpeta `.github` está oculta en Finder. Usa Cmd + Shift + . para verla.
3. En GitHub abre Actions → Refresh contribution skyline → Run workflow.

El contenido completo se muestra como una imagen SVG crema y negra. Los botones inferiores son enlaces funcionales. Los títulos de proyectos y contactos dentro de la imagen son texto, no enlaces individuales. La versión se entrega estática, sin texto animado ni servicios externos de insignias. El fondo exterior y el espacio entre bloques pertenecen a GitHub y siguen el tema del visitante.

Se incluyen datos reales del calendario público y un workflow diario. No se ha ejecutado todavía en tu repositorio. El workflow actualiza el gráfico y vuelve a componer la imagen completa a las 09:23 UTC (03:23 en Ciudad de México), sujeto a retrasos y reglas de GitHub Actions. Usa el token automático del repositorio para guardar las imágenes; no tienes que crear un token personal.

Para editar el texto modifica `scripts/compose_readme.py` y ejecuta:

```sh
python3 scripts/compose_readme.py
```

Para actualizar también los datos:

```sh
python3 scripts/contribution_skyline.py Seebaastiaan
python3 scripts/compose_readme.py
```

Python 3.10+, biblioteca estándar, compatible con macOS/Linux/Windows. El generador del calendario depende de la estructura pública del HTML de GitHub. Los conteos no son exclusivamente commits ni miden productividad; la racha y el máximo se calculan sobre el periodo mostrado.
