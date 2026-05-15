# Compilador Automático de Kernel Linux Vanilla 7.0.7 para Linux Mint

Script Python que descarga, compila e instala el kernel Linux Vanilla 7.0.7 en Linux Mint de forma completamente automática, generando paquetes `.deb` nativos.

---

## Índice

- [Descripción](#descripción)
- [Requisitos del sistema](#requisitos-del-sistema)
- [Instalación de dependencias](#instalación-de-dependencias)
- [Uso](#uso)
- [Configuración](#configuración)
- [Proceso paso a paso](#proceso-paso-a-paso)
- [Referencia de funciones](#referencia-de-funciones)
- [Estructura de archivos generados](#estructura-de-archivos-generados)
- [Solución de problemas](#solución-de-problemas)

---

## Descripción

Este script automatiza completamente el proceso de compilación del kernel Linux Vanilla desde las fuentes oficiales de [kernel.org](https://kernel.org), adaptado para su uso en Linux Mint. Utiliza la configuración del kernel actualmente instalado en el sistema como base y genera paquetes `.deb` listos para instalar con `dpkg`.

---

## Requisitos del sistema

- **OS:** Linux Mint (o cualquier distribución basada en Debian/Ubuntu)
- **Python:** 3.6 o superior
- **Privilegios:** Se requiere `sudo` para instalar dependencias y los paquetes `.deb` finales
- **Espacio en disco:** ~25 GB libres (fuentes + compilación + paquetes)
- **RAM recomendada:** 4 GB mínimo (8 GB o más para compilaciones rápidas)

---

## Instalación de dependencias

El script instala las dependencias de compilación automáticamente, pero también se pueden instalar manualmente:

```bash
sudo apt install build-essential libncurses-dev bison flex \
  libssl-dev libelf-dev bc python3 cpio xz-utils \
  python3-requests python3-pip linux-headers-$(uname -r) \
  gcc debhelper libdw-dev rsync dwarves
```

---

## Uso

```bash
python3 script.py
```

El script es completamente autónomo. No requiere intervención manual durante la ejecución.

> **Nota:** Si el archivo `.tar.xz` o el directorio de fuentes ya existen en `~/kernel-builder/`, el script omite la descarga y extracción respectivamente para ahorrar tiempo.

---

## Configuración

Las variables de configuración se encuentran al inicio del script:

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `KERNEL_VERSION` | `7.0` | Versión mayor del kernel |
| `KERNEL_FULL_VERSION` | `7.0.7` | Versión completa del kernel |
| `KERNEL_URL` | `https://cdn.kernel.org/...` | URL de descarga del tarball |
| `WORK_DIR` | `~/kernel-builder/` | Directorio de trabajo principal |
| `SOURCE_ARCHIVE` | `WORK_DIR/linux-7.0.7.tar.xz` | Ruta del archivo descargado |
| `SOURCE_DIR` | `WORK_DIR/linux-7.0.7/` | Ruta del código fuente extraído |
| `DEB_OUTPUT_DIR` | `WORK_DIR/debs/` | Directorio de salida de paquetes `.deb` |

> Si el script se ejecuta con `sudo`, `WORK_DIR` apunta al home del usuario original (`$SUDO_USER`) en lugar de `/root`.

---

## Proceso paso a paso

1. **Detección de CPU** — Ejecuta `lscpu` e imprime el modelo del procesador detectado.
2. **Creación de directorios** — Crea `~/kernel-builder/` y `~/kernel-builder/debs/` si no existen.
3. **Instalación de dependencias** — Instala con `apt` todos los paquetes necesarios para compilar el kernel.
4. **Descarga del kernel** — Descarga `linux-7.0.7.tar.xz` desde `cdn.kernel.org` con barra de progreso. Se omite si el archivo ya existe.
5. **Extracción del código fuente** — Extrae el tarball en `~/kernel-builder/`. Se omite si el directorio ya existe.
6. **Copia de configuración** — Copia `/boot/config-$(uname -r)` como `.config` base en el directorio de fuentes.
7. **Actualización de configuración** — Ejecuta `make olddefconfig` para adaptar la config al nuevo kernel sin intervención manual.
8. **Compilación del kernel** — Compila con `make -j<núcleos>` usando todos los núcleos disponibles del sistema.
9. **Generación de paquetes `.deb`** — Ejecuta `make bindeb-pkg` para generar paquetes instalables y los mueve a `debs/`.
10. **Instalación** — Instala los `.deb` generados con `sudo dpkg -i`.
11. **Fin** — Se solicita reiniciar el sistema para arrancar con el nuevo kernel.

---

## Referencia de funciones

### `run_command(command, cwd=None)`
Ejecuta un comando del sistema como subproceso, mostrando la salida en tiempo real. Lanza una excepción si el código de retorno es distinto de cero.

- **`command`**: Lista de strings con el comando y sus argumentos.
- **`cwd`**: Directorio de trabajo opcional para el proceso.

---

### `detect_cpu()`
Obtiene información del procesador usando `lscpu` e imprime el nombre del modelo. Devuelve la salida completa de `lscpu` como string.

---

### `create_directories()`
Crea los directorios `WORK_DIR` y `DEB_OUTPUT_DIR` si no existen, incluyendo directorios intermedios.

---

### `download_kernel()`
Descarga el archivo `.tar.xz` del kernel desde `KERNEL_URL` con seguimiento de progreso en MB. Lanza excepción si la respuesta HTTP no es 200.

---

### `extract_kernel()`
Extrae el archivo `SOURCE_ARCHIVE` en `WORK_DIR` usando el módulo `tarfile` de Python.

---

### `prepare_config()`
Copia el archivo de configuración del kernel actualmente en uso (`/boot/config-$(uname -r)`) al directorio de fuentes como `.config`.

---

### `update_config()`
Ejecuta `make olddefconfig` en el directorio de fuentes para actualizar automáticamente la configuración a las opciones por defecto del nuevo kernel.

---

### `install_build_deps()`
Instala mediante `apt` todas las dependencias de compilación necesarias: `build-essential`, `libncurses-dev`, `bison`, `flex`, `libssl-dev`, `libelf-dev`, `bc`, `cpio`, `xz-utils`, `debhelper`, `libdw-dev`, `rsync`, `dwarves`.

---

### `build_kernel()`
Compila el kernel usando todos los núcleos del sistema (`make -j<núcleos>`).

---

### `build_deb()`
Genera paquetes `.deb` mediante `make bindeb-pkg` con la versión `7.0.7-custom`. Mueve los `.deb` generados a `DEB_OUTPUT_DIR`.

---

### `install_kernel()`
Busca todos los `.deb` en `DEB_OUTPUT_DIR` y los instala con `sudo dpkg -i`. Informa si no se encuentran paquetes.

---

### `main()`
Función principal. Orquesta la ejecución de todas las funciones anteriores en orden, con comprobaciones de idempotencia para descarga y extracción.

---

## Estructura de archivos generados

```text
~/kernel-builder/
├── linux-7.0.7.tar.xz               ← tarball descargado
├── linux-7.0.7/                      ← código fuente extraído
│   ├── .config                       ← configuración del kernel
│   └── ...                           ← resto de fuentes
└── debs/                             ← paquetes instalables
    ├── linux-image-7.0.7-custom_*.deb
    ├── linux-headers-7.0.7-custom_*.deb
    └── linux-libc-dev_*.deb
```

---

## Solución de problemas

**Error al descargar el kernel**
Verifica conectividad y que la URL del kernel sea válida. Linux 7.x puede no existir aún; ajusta `KERNEL_FULL_VERSION` y `KERNEL_URL` a una versión estable disponible en [kernel.org](https://kernel.org).

**Error en `prepare_config`: archivo no encontrado**
El archivo `/boot/config-$(uname -r)` no existe. Instala el paquete `linux-image-$(uname -r)` o copia manualmente un `.config` válido.

**Compilación lenta**
Normal. En hardware moderno puede tardar entre 30 minutos y varias horas según los núcleos disponibles.

**Error `dpkg` al instalar**
Resuelve dependencias rotas con:
```bash
sudo apt --fix-broken install
```
