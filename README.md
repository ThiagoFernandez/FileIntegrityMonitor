# fileIntegrityMonitor

Monitor de integridad de archivos de línea de comandos construido en Python. Genera una baseline de hashes criptográficos de un directorio y detecta cualquier modificación, eliminación, creación o renombre de archivos en verificaciones posteriores.

Proyecto de la Fase 1 del roadmap de Python para ciberseguridad — el mismo mecanismo que usan herramientas empresariales como Tripwire y OSSEC.

---

## Features

- **Tres modos de operación:** `Crear`, `Verificar`, `Watch`
- **Detección de cinco tipos de cambio:** modificados, eliminados, nuevos, renombrados y sin acceso (el archivo existe pero ya no se puede leer)
- **Detección de renombres con score de confianza** (ALTA/MEDIA/BAJA) basado en directorio, nombre, extensión y unicidad del hash, con emparejamiento 1 a 1
- **Resolución automática de renombres** — actualiza el baseline con los renombres confirmados
- **Symlinks sin seguir** — se vigila hacia dónde apunta el link, no el contenido del destino
- **Guardado atómico** del baseline (no queda un JSON cortado si algo falla)
- **Multithreading** adaptativo — workers según CPU disponibles
- **Barra de progreso** en tiempo real durante el hashing
- **Alertas con nivel de severidad** — HIGH / MEDIUM / LOW / INFO
- **Modo Watch** con dos estrategias: Soft (baseline fijo) y Aggressive (se actualiza con cada cambio)
- **Log append-only** de todas las operaciones (`baseline.log`)
- **Filtro de extensiones** — selección interactiva de extensiones a ignorar
- **Soporte para múltiples algoritmos** — SHA-256, SHA-512, BLAKE2b, SHA3, MD5, SHA-1

---

## Instalación

```bash
git clone https://github.com/ThiagoFernandez/FileIntegrityMonitor.git
cd FileIntegrityMonitor
python main.py
```

Sin dependencias externas — solo biblioteca estándar de Python.

---

## Uso

```bash
python main.py
```

El programa presenta un menú interactivo:

```
1. Crear
2. Verificar
3. Watch
4. Exit
```

### Crear baseline

Seleccionás el directorio, el algoritmo de hash y las extensiones a ignorar. Genera `baseline_<directorio>.json`.

### Verificar

Recalcula los hashes del directorio y compara contra el baseline guardado. Reporta:
- Archivos **modificados** con hash anterior y nuevo
- Archivos **eliminados**
- Archivos **nuevos**
- Posibles **renombres** con score de confianza
- `Todo OK` si no hay cambios

### Watch

Monitoreo continuo cada N segundos. No pide confirmaciones (la resolución de renombres es solo para Verificar), y Ctrl+C vuelve al menú en cualquier momento.

**Soft** (default, Enter): el baseline de referencia no cambia — todos los cambios se siguen reportando en cada ciclo hasta que recreés el baseline manualmente.

**Aggressive**: el baseline se actualiza con cada ciclo — solo alerta sobre cambios nuevos desde la última verificación.

---

## Output

### Terminal — verificación con cambios

```
==================================================
[IDS ALERT] Level: HIGH
Directory: proyecto
==================================================

Modified: 1
 - /home/usuario/proyecto/config.py
   OLD: b94d27b9934d3e08...
   NEW: 1a3db2c45f8e92a1...

DELETED (1):
 - /home/usuario/proyecto/utils.py

NEW (1):
 - /home/usuario/proyecto/helpers.py

RENAMED (1):
 - [ALTA] /home/usuario/proyecto/old_name.py → /home/usuario/proyecto/new_name.py

SIN ACCESO (1):
 - /home/usuario/proyecto/secreto.key
```

Los renombres se descuentan de DELETED y NEW: un archivo renombrado aparece solo en RENAMED.

### Niveles de severidad

| Nivel | Condición |
|-------|-----------|
| HIGH | Hay archivos modificados o eliminados |
| MEDIUM | Archivos nuevos o sin acceso |
| LOW | Solo posibles renombres |
| INFO | Sin cambios relevantes |

### baseline.json

```json
{
    "metadata": {
        "creado": "2026-04-30_21-00-00",
        "directorio": "proyecto",
        "algoritmo": "sha256",
        "total_archivos": 15,
        "ignore_ext": [".log", ".tmp"]
    },
    "archivos": {
        "/home/usuario/proyecto/main.py": "b94d27b9934d3e08...",
        "/home/usuario/proyecto/config.py": "1a3db2c45f8e92a1..."
    },
    "sin_acceso": []
}
```

### baseline.log

```
Time: 2026-04-30_21-00-00 | Action: crear | Directory: proyecto | Modified=0 Eliminated=0 New=0 Renamed=0
Time: 2026-04-30_21-05-00 | Action: verificar | Directory: proyecto | Modified=1 Eliminated=1 New=1 Renamed=1
```

---

## Cómo funciona

### Hashing en chunks

Los archivos se leen en bloques de 8KB para no cargar archivos grandes en memoria de una vez. Compatible con archivos de cualquier tamaño.

### Detección de renombres

Un renombre se detecta cuando un archivo desaparece y aparece uno nuevo con el mismo hash. El score de confianza se calcula así:

| Criterio | Puntos |
|----------|--------|
| Hash igual (base) | +50 |
| Mismo directorio (renombrado) o mismo nombre en otro directorio (movido) | +30 |
| Misma extensión | +10 |
| El hash es único entre eliminados y nuevos | +10 |
| El hash se repite (ej. archivos vacíos o copias) | −20 |

El tamaño no se usa: mismo hash implica mismo tamaño. Los candidatos se emparejan 1 a 1 de mayor a menor score, así que cada archivo participa en un solo renombre.

Score ≥ 80 → ALTA (la resolución automática los aplica al baseline)
Score ≥ 60 → MEDIA
Score < 60 → BAJA

### Multithreading

El número de workers se calcula dinámicamente: `min(64, cpu_count * 8)`. En un sistema de 4 núcleos usa hasta 32 workers en paralelo.

---

## Algoritmos soportados

| Algoritmo | Recomendado |
|-----------|-------------|
| sha256 | ✅ Uso general |
| sha512 | ✅ Alta seguridad |
| blake2b | ✅ Más rápido que sha512 |
| sha3_256 | ✅ Estándar moderno |
| sha3_512 | ✅ Estándar moderno |
| md5 | ⚠️ Solo checksums, no para seguridad |
| sha1 | ⚠️ Deprecado, evitar |

---

*Parte del roadmap de Python para Ciberseguridad — Fase 1*
