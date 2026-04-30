import hashlib
import os
import json
from datetime import datetime

def get_time():
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
    return current_time

def guardar_json(data, directorio):
    with open(f"baseline_{directorio}.json", "wt", encoding="UTF-8") as f:
        json.dump(data, f, indent=4)
    print("baseline guardado con exito")

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

def crear_baseline(directorio, algoritmo):
    baseline = {
        "metadata": {
            "creado": get_time(),
            "directorio": directorio,
            "algoritmo": algoritmo,
            "total_archivos": None
        },
        "archivos": {}
    }
    total = 0
    for root, _, files in os.walk(directorio):
        for nombre in files:
            ruta = os.path.abspath(os.path.join(root, nombre))
            try:
                h = hash_archivo(ruta, algoritmo)
                if h: # evita guardar None
                    baseline["archivos"][ruta] = h
                    total+=1
            except (PermissionError, FileNotFoundError) as e:
                print(f"[WARN] No se pudo leer {ruta}: {e}")
    baseline["metadata"]["total_archivos"]= total
    return baseline

def crear():
    directorio = seleccionar_directorio()
    if directorio == -1:
        return -1

    algoritmo = elegir_algoritmo()
    if algoritmo == -1:
        return -1

    baseline = crear_baseline(directorio, algoritmo)

    guardar_json(baseline, directorio)

def recuperar_algoritmo(directorio):
    try:
        with open(directorio, "rt", encoding="UTF-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"[ERROR] No se pudo leer baseline: {e}")
        return -1

def contar_nuevos(archivos_old, archivos_new):
    state = 0
    nuevos = []
    for arch_new in archivos_new:
        igual = False
        for arch_old in archivos_old:
            if arch_new == arch_old: 
                igual = True
                break
        if not igual:
            nuevos.append(arch_new)
    
    if len(nuevos) != 0:
        state = -1
        print("Hay archivos nuevos | Se sugiere revisarlos y decidir si hacer o no un baseline actualizado")
        for idx, value in enumerate(nuevos):
            print(f"{idx+1}. {value}")
    return state

def contar_eliminados_modificados(archivos_old, archivos_new, data, baseline):
    state = 0 # all good

    eliminados = []
    modificados = []
    for arch_old in archivos_old:
        igual = False
        for arch_new in archivos_new:
            if arch_new == arch_old: 
                igual = True
                if data["archivos"][arch_old] != baseline["archivos"][arch_new]:
                    modificados.append((arch_old,data["archivos"][arch_old], arch_new), baseline["archivos"][arch_new])
                break
        if not igual:
            eliminados.append(arch_old)
    
    if len(modificados) != 0:
        state = -1
        print("Hay archivos modificados | Se sugiere revisarlos y decidir si hacer o no un baseline actualizado")
        for idx, value in enumerate(modificados):
            print(f"{idx+1}. Viejo: {value[0]} - Hash: {value[1]} | Nuevo: {value[2]} - Hash: {value[3]}")
    
    if len(eliminados) != 0:
        state = -1
        print("Hay archivos eliminados | Se sugiere revisarlos y decidir si hacer o no un baseline actualizado")
        for idx, value in enumerate(eliminados):
            print(f"{idx+1}. {value}")

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

def comparar_baselines(data, baseline):
    all_good = True
    archivos_old = list(data["archivos"].keys())
    archivos_new = list(baseline["archivos"].keys())

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


def verificar():
    directorio = seleccionar_directorio()
    if directorio == -1:
        return -1
    
    file_name = "baseline_"+directorio+".json"
    data = recuperar_algoritmo(file_name)
    if data == -1:
        return -1
    
    algoritmo = data["metadata"]["algoritmo"]
    baseline = crear_baseline(directorio, algoritmo)

    if comparar_baselines(data, baseline):
        print("Todo OK")

def main():
    while True:
        show_options(["Crear","Verificar"])
        match validate_number([1, 2]):
            case -1:
                break
            case 1:
                crear()
                print("termino crear")
            case 2:
                verificar()
                print("termino verificar")
                # si se encuentra alguna modificacion, se da la opcion de hacer un baseline nuevo o volver para atras estilo git, y te muestra que linea del archivo cambio (no se como porque el archivo no lo tengo mas al menos que se haga siempre un backup del dirctorio entero pero eso es algo aparte del programa me parece)

#m.p
if __name__ == "__main__":
    main()
    print("termino main")