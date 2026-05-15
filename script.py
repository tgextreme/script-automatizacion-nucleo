#!/usr/bin/env python3

import os
import subprocess
import requests
import tarfile
from pathlib import Path

# =========================================================
# CONFIGURACIÓN
# =========================================================

KERNEL_VERSION = "7.0"
KERNEL_FULL_VERSION = "7.0.7"

KERNEL_URL = (
    f"https://cdn.kernel.org/pub/linux/kernel/v7.x/"
    f"linux-{KERNEL_FULL_VERSION}.tar.xz"
)

WORK_DIR = Path(os.environ.get("SUDO_USER") and f"/home/{os.environ['SUDO_USER']}" or str(Path.home())) / "kernel-builder"
SOURCE_ARCHIVE = WORK_DIR / f"linux-{KERNEL_FULL_VERSION}.tar.xz"
SOURCE_DIR = WORK_DIR / f"linux-{KERNEL_FULL_VERSION}"
DEB_OUTPUT_DIR = WORK_DIR / "debs"

# =========================================================
# UTILIDADES
# =========================================================

def run_command(command, cwd=None):
    """
    Ejecuta comandos del sistema mostrando salida en tiempo real.
    """

    print(f"\n[+] Ejecutando: {' '.join(command)}\n")

    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout:
        print(line, end="")

    process.wait()

    if process.returncode != 0:
        raise Exception(f"Error ejecutando comando: {' '.join(command)}")


# =========================================================
# DETECCIÓN CPU
# =========================================================

def detect_cpu():
    """
    Detecta el procesador actual.
    """

    print("[+] Detectando CPU...\n")

    cpuinfo = subprocess.check_output(["lscpu"], text=True)

    for line in cpuinfo.splitlines():
        if "Model name" in line:
            print(f"[CPU] {line.split(':')[1].strip()}")

    return cpuinfo


# =========================================================
# CREAR DIRECTORIOS
# =========================================================

def create_directories():
    """
    Crea estructura de trabajo.
    """

    print(f"[+] Creando directorios de trabajo...")

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    DEB_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# DESCARGAR KERNEL
# =========================================================

def download_kernel():
    """
    Descarga kernel vanilla desde kernel.org
    """

    print(f"\n[+] Descargando kernel:\n{KERNEL_URL}\n")

    response = requests.get(KERNEL_URL, stream=True)

    if response.status_code != 200:
        raise Exception("No se pudo descargar el kernel")

    total = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(SOURCE_ARCHIVE, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):

            if chunk:
                f.write(chunk)
                downloaded += len(chunk)

                mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)

                print(f"\rDescargado: {mb:.2f} MB / {total_mb:.2f} MB", end="")

    print("\n[+] Descarga completada")


# =========================================================
# EXTRAER KERNEL
# =========================================================

def extract_kernel():
    """
    Extrae el código fuente.
    """

    print("\n[+] Extrayendo kernel...")

    with tarfile.open(SOURCE_ARCHIVE) as tar:
        tar.extractall(WORK_DIR)

    print("[+] Kernel extraído")


# =========================================================
# COPIAR CONFIG ACTUAL
# =========================================================

def prepare_config():
    """
    Usa configuración actual del sistema.
    """

    print("\n[+] Preparando configuración del kernel...")

    current_config = f"/boot/config-{os.uname().release}"
    destination = SOURCE_DIR / ".config"

    run_command([
        "cp",
        current_config,
        str(destination)
    ])

    print("[+] Configuración copiada")


# =========================================================
# ACTUALIZAR CONFIG
# =========================================================

def update_config():
    """
    Actualiza configuración automáticamente.
    """

    print("\n[+] Actualizando configuración...")

    run_command(
        ["make", "olddefconfig"],
        cwd=SOURCE_DIR
    )


# =========================================================
# COMPILAR KERNEL
# =========================================================

def build_kernel():
    """
    Compila el kernel.
    """

    cores = os.cpu_count()

    print(f"\n[+] Compilando usando {cores} núcleos...\n")

    run_command(
        ["make", f"-j{cores}"],
        cwd=SOURCE_DIR
    )


# =========================================================
# DEPENDENCIAS DE COMPILACIÓN
# =========================================================

def install_build_deps():
    """
    Instala las dependencias necesarias para compilar el kernel y generar .deb
    """

    print("[+] Instalando dependencias de compilación...\n")

    deps = [
        "build-essential", "libncurses-dev", "bison", "flex",
        "libssl-dev", "libelf-dev", "bc", "cpio", "xz-utils",
        "debhelper", "libdw-dev", "rsync", "dwarves"
    ]

    run_command(["sudo", "apt", "install", "-y"] + deps)


# =========================================================
# GENERAR PAQUETES .DEB
# =========================================================

def build_deb():
    """
    Genera paquetes .deb para Linux Mint.
    """

    cores = os.cpu_count()

    print("\n[+] Generando paquetes .deb...\n")

    run_command(
        [
            "make",
            f"-j{cores}",
            "bindeb-pkg",
            f"KDEB_PKGVERSION={KERNEL_FULL_VERSION}-custom"
        ],
        cwd=SOURCE_DIR
    )

    # Mover .deb generados al directorio de salida
    for deb in WORK_DIR.glob("*.deb"):
        deb.rename(DEB_OUTPUT_DIR / deb.name)
        print(f"[+] Paquete listo: {DEB_OUTPUT_DIR / deb.name}")


# =========================================================
# MAIN
# =========================================================

def install_kernel():
    """
    Instala los paquetes .deb generados.
    """

    debs = list(DEB_OUTPUT_DIR.glob("*.deb"))

    if not debs:
        print("[!] No se encontraron paquetes .deb para instalar")
        return

    print("\n[+] Instalando paquetes .deb...\n")

    run_command(["sudo", "dpkg", "-i"] + [str(d) for d in debs])

    print("\n[+] Kernel instalado correctamente")
    print("[+] Reinicia el sistema para usar el nuevo kernel")


def main():

    print("""
=================================================
 Linux Mint Kernel Builder
 Kernel Vanilla Linux 7.0.7
=================================================
""")

    detect_cpu()
    create_directories()
    install_build_deps()

    # Descargar solo si no existe ya el archivo
    if not SOURCE_ARCHIVE.exists():
        download_kernel()
    else:
        print(f"[+] Archivo ya descargado: {SOURCE_ARCHIVE}")

    # Extraer solo si no existe ya el directorio fuente
    if not SOURCE_DIR.exists():
        extract_kernel()
    else:
        print(f"[+] Fuentes ya extraídas: {SOURCE_DIR}")

    prepare_config()
    update_config()
    build_kernel()
    build_deb()
    install_kernel()

    print("""
=================================================
 ¡Proceso completado!
=================================================
 Reinicia el sistema para arrancar con el nuevo kernel.
""")


if __name__ == "__main__":
    main()