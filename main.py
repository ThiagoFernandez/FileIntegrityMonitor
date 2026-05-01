import hashlib
import os
import json
import time
import sys
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from datetime import datetime

def procesar_archivo(args):
    ruta, algoritmo = args
    try:
        h = hash_archivo(ruta, algoritmo)
        return ruta, h
    except Exception:
        return ruta, None

def mostrar_progreso(procesados, total, ancho=30):
    porcentaje = procesados / total
    llenos = int(ancho * porcentaje)
    barra = "#" * llenos + "-" * (ancho - llenos)

    sys.stdout.write(
        f"\r[{barra}] {porcentaje*100:6.2f}% | {procesados}/{total} archivos"
    )
    sys.stdout.flush()

def get_time():
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
    return current_time

def guardar_json(data, directorio):
    with open(f"baseline_{directorio}.json", "wt", encoding="UTF-8") as f:
        json.dump(data, f, indent=4)
    print("baseline guardado con exito")

def guardar_log(directorio, action, modificados=None, eliminados=None, nuevos=None, posibles=None):
    modificados = modificados or []
    eliminados = eliminados or []
    nuevos = nuevos or []
    posibles = posibles or []

    with open("baseline.log", "at", encoding="UTF-8") as f:
        f.write(
            f"Time: {get_time()} | Action: {action} | Directory: {directorio} | "
            f"Modified={len(modificados)} Eliminated={len(eliminados)} "
            f"New={len(nuevos)} Renamed={len(posibles)}\n"
        )

def hash_archivo(ruta, algoritmo='sha256'):
    '''
    carga el archivo a hashear, lo divide x partes(chunks) por si es muy grande y no detone la ram y va agregando el hash x cada chunk. POr ultimo lo devuelve en hexadecimal
    '''
    h = hashlib.new(algoritmo)
    try:
        with open(ruta, "rb") as f:
            while chunk:= f.read(8192): # walrus op y 8KB x chunk
                h.update(chunk)
    except Exception as e:
        print(f"Error leyendo {ruta}: {e}")
        return None
    return h.hexdigest()  

def validate_number(options):
    while True:
        try:
            option = int(input("Choose an option: "))
        except ValueError:
            print("The value must be a number | Try again")
        else:
            if option < 1 or option > len(options)+1:
                print(f"The option must be between 1-{len(options)+1} | Try again")
            elif option == len(options)+1:
                return -1
            else:
                return option
            
def show_options(options):
    for idx, value in enumerate(options):
        print(f"{idx+1}. {value}")
    print(f"{len(options)+1}. Exit")

def seleccionar_directorio():
    directorios = [d for d in os.listdir("./") if os.path.isdir(d)]
    show_options(directorios)
    opt = validate_number(directorios)
    if opt == -1:
        return -1
    else:
        return directorios[opt-1]

def elegir_algoritmo():
    algoritmos = ['md5', 'sha1', 'sha256', 'sha512', 'sha3_256', 'sha3_512', 'blake2b', 'blake2s'] # btw solo usen sha256, sha512 y blake2
    show_options(algoritmos)
    op = validate_number(algoritmos)
    if op == -1:
        return -1
    else:
        return algoritmos[op-1]

def crear_baseline(directorio, algoritmo, ignore_ext):
    baseline = {
        "metadata": {
            "creado": get_time(),
            "directorio": directorio,
            "algoritmo": algoritmo,
            "total_archivos": 0,
            "ignore_ext": ignore_ext
        },
        "archivos": {}
    }

    rutas = []

    for root, _, files in os.walk(directorio):
        for nombre in files:
            ruta = os.path.abspath(os.path.join(root, nombre))
            _, ext = os.path.splitext(nombre)

            if ext in ignore_ext:
                continue

            rutas.append(ruta)

    total = len(rutas)

    if total == 0:
        print("No hay archivos para procesar")
        return baseline

    print(f"\nProcesando {total} archivos...\n")

    procesados = 0

    # multithreading
    max_workers = min(64, (os.cpu_count() or 2) * 8)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(procesar_archivo, (ruta, algoritmo)) for ruta in rutas]

        for future in as_completed(futures):
            try:
                ruta, h = future.result()
            except Exception:
                continue

            if h:
                baseline["archivos"][ruta] = h
                baseline["metadata"]["total_archivos"] += 1

            procesados += 1
            mostrar_progreso(procesados, total)

    print("\n\n✔ Baseline completado\n")

    return baseline

def crear():
    directorio = seleccionar_directorio()
    if directorio == -1:
        return

    algoritmo = elegir_algoritmo()
    if algoritmo == -1:
        return

    print("\nSeleccionar extensiones a ignorar:")
    ignore_ext = filter_extension()

    baseline = crear_baseline(directorio, algoritmo, ignore_ext)

    guardar_json(baseline, directorio)
    guardar_log(directorio, "crear")

def recuperar_algoritmo(directorio):
    try:
        with open(directorio, "rt", encoding="UTF-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"[ERROR] No se pudo leer baseline: {e}")
        return -1

def contar_nuevos(archivos_old, archivos_new):
    nuevos = [arch for arch in archivos_new if arch not in archivos_old]

    if nuevos:
        print("\nArchivos nuevos:")
        for i, n in enumerate(nuevos, 1):
            print(f"{i}. {n}")

    return nuevos

def contar_eliminados_modificados(archivos_old, archivos_new, data, baseline):
    eliminados = []
    modificados = []

<<<<<<< HEAD
    return state, eliminados

def contar_renombre(eliminados, nuevos, data, baseline):
    posible_renombre = []
    state = 0
    for elim in eliminados:
        for nue in nuevos:
            if data["archivos"][elim] == baseline["archivos"][nue]:
                posible_renombre.append((elim, nue))
    
    if len(posible_renombre)!=0:
        state = -1
        print("Hay archivos que pueden ser que hayan sido renombrados | Se sugiere revisarlos y decidir si hacer o no un baseline actualizado")
        for idx, value in enumerate(posible_renombre):
            print(f"{idx+1}. {value}")
    
    return state
=======
    for old in archivos_old:
        if old not in archivos_new:
            eliminados.append(old)
        else:
            if data["archivos"][old] != baseline["archivos"][old]:
                modificados.append((old, data["archivos"][old], baseline["archivos"][old]))
>>>>>>> 51c19ee (Finished)

    if modificados:
        print("\nArchivos modificados:")
        for i, (ruta, h_old, h_new) in enumerate(modificados, 1):
            print(f"{i}. {ruta}\n   OLD: {h_old}\n   NEW: {h_new}")

    if eliminados:
        print("\nArchivos eliminados:")
        for i, e in enumerate(eliminados, 1):
            print(f"{i}. {e}")

    return modificados, eliminados

def clasificar(score):
    if score >= 80:
        return "ALTA"
    elif score >= 60:
        return "MEDIA"
    else:
        return "BAJA"

def calcular_confianza(old, new):
    score = 50  # hash igual ya validado

    if os.path.basename(old) == os.path.basename(new):
        score += 30

    if old.split('.')[-1] == new.split('.')[-1]:
        score += 10

    if os.path.dirname(old) == os.path.dirname(new):
        score += 5

    try:
        if os.path.getsize(old) == os.path.getsize(new):
            score += 5
    except:
        pass

    return score

def contar_renombre(eliminados, nuevos, data, baseline):
    posibles = []

    for elim in eliminados:
        hash_old = data["archivos"][elim]

        for nue in nuevos:
            if hash_old == baseline["archivos"][nue]:
                score = calcular_confianza(elim, nue)
                posibles.append((elim, nue, score, clasificar(score)))

    if posibles:
        print("\nPosibles renombres:")
        for i, (old, new, score, nivel) in enumerate(posibles, 1):
            print(f"{i}. [{nivel}] {old} → {new} ({score})")

    return posibles

def automatic_resolution(posibles, eliminados, nuevos):
    confirmados = []

    usados_new = set()

    for old, new, score, nivel in posibles:
        if nivel == "ALTA" and new not in usados_new:
            confirmados.append((old, new))
            usados_new.add(new)

    eliminados_rest = [e for e in eliminados if e not in [c[0] for c in confirmados]]
    nuevos_rest = [n for n in nuevos if n not in usados_new]

    print("\nRenombres confirmados automáticamente:")
    for old, new in confirmados:
        print(f"{old} → {new}")

    return confirmados, eliminados_rest, nuevos_rest


def aplicar_resolucion(data, confirmados):
    for old, new in confirmados:
        if old in data["archivos"]:
            hash_val = data["archivos"][old]

            del data["archivos"][old]

            data["archivos"][new] = hash_val

    print("\nBaseline actualizado con renombres confirmados")

    guardar_json(data, data["metadata"]["directorio"]+"_updated")

def comparar_baselines(data, baseline, directorio):
    archivos_old = list(data["archivos"].keys())
    archivos_new = list(baseline["archivos"].keys())

<<<<<<< HEAD
    state1, eliminados= contar_eliminados_modificados(archivos_old, archivos_new, data, baseline)
    state2, nuevos = contar_nuevos(archivos_old, archivos_new)
    state3 = contar_renombre(eliminados, nuevos, data, baseline)
    if state1 == -1:
        all_good = False
    if state2 == -1:
        all_good = False
    if state3 == -1:
        all_good = False
    return all_good
=======
    modificados, eliminados = contar_eliminados_modificados(
        archivos_old, archivos_new, data, baseline
    )
>>>>>>> 51c19ee (Finished)

    nuevos = contar_nuevos(archivos_old, archivos_new)

    posibles = contar_renombre(eliminados, nuevos, data, baseline)

    guardar_log(directorio, "verificar", modificados, eliminados, nuevos, posibles)

    if not modificados and not eliminados and not nuevos:
        return True
    else:
        alert(directorio, modificados, eliminados, nuevos, posibles)

    if posibles:
        show_options(["Automatic resolution"])
        rt = validate_number(["1"])

        if rt != -1:
            confirmados, eliminados_rest, nuevos_rest = automatic_resolution(
                posibles, eliminados, nuevos
            )

            aplicar_resolucion(data, confirmados)

    return False

def filter_extension():
    all_extensions = [
        ".txt",".md",".csv",".log",".json",".xml",".yaml",".yml",
        ".ini",".cfg",".conf",".env",
        ".py",".pyc",".pyo",".js",".ts",".html",".css",
        ".java",".c",".cpp",".h",".cs",".php",".rb",".go",".rs",
        ".swift",".kt",".sh",".bash",".zsh",
        ".db",".sqlite",".sqlite3",".sql",
        ".zip",".tar",".gz",".bz2",".xz",".rar",".7z",
        ".jpg",".jpeg",".png",".gif",".bmp",".webp",".svg",".ico",
        ".mp3",".wav",".ogg",".flac",".aac",
        ".mp4",".mkv",".avi",".mov",".wmv",".webm",
        ".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx",
        ".exe",".dll",".so",".bin",".dat",
        ".tmp",".cache",".swp",".bak",".old",".out",".lock"
    ]

    ignore_ext = set()

    while True:
        show_options(all_extensions)
        op = validate_number(all_extensions)

        if op == -1:
            break

        ignore_ext.add(all_extensions[op-1])
        all_extensions.pop(op-1)

    return ignore_ext

def severity_calculator(modified, eliminated, new, posible):
    if modified or eliminated:
         return "HIGH"
    elif new:
        return "MEDIUM"
    elif posible:
        return "LOW"
    return "INFO"

def alert(directory, modified, eliminated, new, posible):
    severity = severity_calculator(modified, eliminated, new, posible)

    print("\n"+"="*50)
    print(f"[IDS ALERT] Level: {severity}")
    print(f"Directory: {directory}")
    print("="*50)

    if modified:
        print(f"\nModified: {len(modified)}")
        for r, _, _ in modified:
            print(f" - {r}")

    if eliminated:
        print(f"\nDELETED ({len(eliminated)}):")
        for r in eliminated:
            print(f" - {r}")

    if new:
        print(f"\nNEW ({len(new)}):")
        for r in new:
            print(f" - {r}")

    if posible:
        print(f"\nRENAMED ({len(posible)}):")
        for old, new, _, nivel in posible:
            print(f" - [{nivel}] {old} → {new}")
    
    print("\a") # ts ring t terminal I think

def verificar():
    directorio = seleccionar_directorio()
    if directorio == -1:
        return
    
    file_name = f"baseline_{directorio}.json"
    data = recuperar_algoritmo(file_name)
    if data == -1:
        return
    
    algoritmo = data["metadata"]["algoritmo"]

    
    ignore_ext = set(data["metadata"].get("ignore_ext", []))

    baseline = crear_baseline(directorio, algoritmo, ignore_ext)

    if comparar_baselines(data, baseline, directorio):
        print("Todo OK")

def choose_mode():
    print("Soft is the default")
    opt = ["Aggressive", "Soft"]
    show_options(opt)
    rt = validate_number(opt)
    if rt == -1:
        return -1
    else:
        return opt[rt-1]
def watch(mode):
    directorio = seleccionar_directorio()
    if directorio == -1:
        return

    file_name = f"baseline_{directorio}.json"
    data = recuperar_algoritmo(file_name)
    if data == -1:
        return

    algoritmo = data["metadata"]["algoritmo"]
    ignore_ext = set(data["metadata"].get("ignore_ext", []))

    try:
        intervalo = int(input("Intervalo en segundos: "))
    except ValueError:
        print("Valor inválido")
        return

    print(f"\n[WATCH MODE] Monitoreando '{directorio}' cada {intervalo}s...\n")

    while True:
        start_time = time.time()
        baseline_actual = crear_baseline(directorio, algoritmo, ignore_ext)

        cambios = not comparar_baselines(data, baseline_actual, directorio)
        end_time = time.time()
        print(f"Process duration: {end_time - start_time}")
        if cambios:
            print("\nCAMBIOS DETECTADOS \a")
            if mode == "Aggressive":
                data = baseline_actual
        try:
            print("CONTROL + C to go back")
            time.sleep(intervalo)
        except KeyboardInterrupt:
            print("\nBACK TO THE MENU")
            break
def main():
    while True:
        show_options(["Crear","Verificar", "Watch"])
        match validate_number([1, 2, 3]):
            case -1:
                break
            case 1:
                crear()
            case 2:
                verificar()
            case 3:
                mode = choose_mode()
                if mode != -1:
                    watch(mode)

#m.p
if __name__ == "__main__":
    main()