"""
UTN FRT - Tecnicatura Universitaria en Programación
Introducción al Análisis de Datos - TP N° 2: Limpieza y preparación de datos
Caso integrador: Club Deportivo Cerro Alto (padrón de socios y cuotas)

Qué hace este script:
  1. Lee el padrón original de la cátedra (datos/*.xlsx, sin modificar).
  2. Aplica el tratamiento a cada problema de calidad, registrando cada decisión en una bitácora.
  3. Agrega transformaciones (tipos de dato y variables derivadas).
  4. Valida el resultado repitiendo la inspección inicial (antes vs. después).
  5. Genera:
       - datos/Registro_Socios_LIMPIO.xlsx   (hojas: socios_limpio, bitacora)
       - tp2_limpieza/informe_tp2.md         (herramienta, bitácora y validación)

Uso (desde la raíz del repo o desde tp2_limpieza):
    python tp2_limpieza/practico.py
"""

from pathlib import Path
import unicodedata

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Configuración
# ----------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
CARPETA_DATOS = RAIZ / "datos"
SALIDA_XLSX = CARPETA_DATOS / "Registro_Socios_LIMPIO.xlsx"
SALIDA_INFORME = Path(__file__).resolve().parent / "informe_tp2.md"

# Fecha de corte del padrón. Se fija a mano (y no con la fecha de hoy) para que
# el resultado sea reproducible. SUPUESTO: cierre del primer semestre 2026.
# Con esta fecha, el alta del 2026-09-30 (socio 119) es posterior al corte.
FECHA_CORTE = pd.Timestamp("2026-06-30")

# Valores que en la planilla significan "dato vacío".
MARCADORES_VACIO = {"—", "–", "-", "", "nan", "none", "n/a", "s/d"}

# Actividades válidas, indexadas por su versión sin tildes y en minúsculas.
ACTIVIDADES_VALIDAS = {
    "padel": "Pádel",
    "futbol 5": "Fútbol 5",
    "natacion": "Natación",
    "basquet": "Básquet",
    "gimnasio": "Gimnasio",
    "tenis": "Tenis",
}

# Categorías válidas (el original mezcla "Activo" y "Activa").
CATEGORIAS_VALIDAS = {
    "activo": "Activo", "activa": "Activo",
    "inactivo": "Inactivo", "inactiva": "Inactivo",
    "cadete": "Cadete",
    "vitalicio": "Vitalicio",
    "honorario": "Honorario",
}

# Un valor de cuota mayor a N veces la mediana de las cuotas positivas se
# considera sospechoso de error de carga.
FACTOR_CUOTA_ATIPICA = 5

COLUMNAS_FINALES = [
    "id_socio", "socio", "dni", "fecha_alta", "anio_alta", "antiguedad_meses",
    "actividad", "categoria", "cuota", "estado", "email", "telefono",
    "observaciones", "revisar",
]

bitacora = []        # una entrada por decisión
marcas = {}          # id_socio -> lista de alertas para la columna "revisar"


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def sin_tildes(texto):
    texto = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def registrar(problema, decision, razon, filas, ids=""):
    """Agrega una decisión a la bitácora."""
    bitacora.append({
        "paso": len(bitacora) + 1,
        "problema": problema,
        "decision": decision,
        "razon": razon,
        "filas_afectadas": int(filas),
        "ids_afectados": ids,
    })


def marcar(id_socio, alerta):
    marcas.setdefault(int(id_socio), []).append(alerta)


def lista_ids(serie):
    return ", ".join(str(int(x)) for x in serie)


def a_texto_numerico(valor):
    """DNI y teléfono: texto de dígitos (Excel a veces los guarda como número)."""
    if pd.isna(valor):
        return np.nan
    texto = str(valor).strip()
    if texto.endswith(".0"):
        texto = texto[:-2]
    return texto


def parsear_cuota(valor):
    """'$ 18.500' -> 18500 ; '$ -18.500' -> -18500 ; ya numérico -> tal cual."""
    if pd.isna(valor):
        return np.nan
    if isinstance(valor, (int, float, np.integer, np.floating)):
        return float(valor)
    texto = str(valor).replace("$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return np.nan


def fecha_valida(valor):
    """Convierte a fecha; devuelve NaT si no existe (ej. 2026-02-30)."""
    if pd.isna(valor):
        return pd.NaT
    texto = str(valor).strip()[:10]
    return pd.to_datetime(texto, format="%Y-%m-%d", errors="coerce")


# ----------------------------------------------------------------------------
# 0. Lectura del original
# ----------------------------------------------------------------------------
def buscar_original():
    candidatos = sorted(
        p for p in CARPETA_DATOS.glob("*.xlsx")
        if "LIMPIO" not in p.name.upper() and not p.name.startswith("~$")
    )
    if not candidatos:
        raise FileNotFoundError(f"No encontré el .xlsx original en {CARPETA_DATOS}")
    if len(candidatos) > 1:
        print("Aviso: hay más de un .xlsx en datos/. Uso:", candidatos[0].name)
    return candidatos[0]


def leer_original(ruta):
    """Lee la planilla ubicando la fila de encabezados (la que empieza con 'ID')."""
    crudo = pd.read_excel(ruta, header=None, dtype=object)
    fila_encabezado = None
    for i in range(len(crudo)):
        if str(crudo.iloc[i, 0]).strip().upper() == "ID":
            fila_encabezado = i
            break
    if fila_encabezado is None:
        raise ValueError("No encontré la fila de encabezados (primera celda 'ID').")

    df = crudo.iloc[fila_encabezado + 1:].copy()
    df.columns = [
        sin_tildes(c).strip().lower().replace(".", "") for c in crudo.iloc[fila_encabezado]
    ]
    df = df.rename(columns={
        "id": "id_socio", "alta": "fecha_alta", "cat": "categoria",
    })
    # Se descartan filas vacías y de pie de página (ID no numérico).
    id_num = pd.to_numeric(df["id_socio"], errors="coerce")
    df = df[id_num.notna()].copy()
    df["id_socio"] = id_num[id_num.notna()].astype(int)
    return df.reset_index(drop=True)


def normalizar_vacios(df):
    """'—', '-', '' y similares pasan a NaN; se recortan espacios."""
    def limpiar(v):
        if pd.isna(v):
            return np.nan
        if isinstance(v, str):
            v = v.strip()
            if v.lower() in MARCADORES_VACIO:
                return np.nan
        return v
    for col in df.columns:
        df[col] = df[col].map(limpiar)
    return df


# ----------------------------------------------------------------------------
# Inspección (se usa ANTES y DESPUÉS para la validación final)
# ----------------------------------------------------------------------------
def inspeccionar(df):
    cuota_num = df["cuota"].map(parsear_cuota)
    positivas = cuota_num[cuota_num > 0]
    umbral = FACTOR_CUOTA_ATIPICA * positivas.median() if len(positivas) else np.inf
    fechas = df["fecha_alta"].map(fecha_valida)
    # Inexistente = había un valor cargado pero no es una fecha real (vacío no cuenta).
    fechas_inexistentes = int((df["fecha_alta"].notna() & fechas.isna()).sum())
    dni_rep = df.duplicated(subset="dni", keep=False)

    resumen = {
        "Filas": len(df),
        "Filas duplicadas (mismo DNI, email, teléfono y alta)": int(
            df.duplicated(subset=["dni", "email", "telefono", "fecha_alta"]).sum()
        ),
        "ID de socio repetidos": int(df["id_socio"].duplicated().sum()),
        "Filas con DNI repetido": int(dni_rep.sum()),
        "Variantes distintas de ACTIVIDAD": int(df["actividad"].nunique()),
        "Variantes distintas de CATEGORÍA (CAT.)": int(df["categoria"].nunique()),
        "Cuotas negativas": int((cuota_num < 0).sum()),
        f"Cuotas atípicas (> {FACTOR_CUOTA_ATIPICA} x mediana)": int((cuota_num > umbral).sum()),
        "Fechas de alta inexistentes (ej. 30 de febrero)": fechas_inexistentes,
        "Fechas de alta posteriores al corte": int((fechas > FECHA_CORTE).sum()),
        "Socios inactivos con cuota pendiente/vencida": int(
            ((df["categoria"] == "Inactivo") & df["estado"].isin(["PENDIENTE", "VENCIDO"])).sum()
        ),
    }
    faltantes = df.isna().sum()
    return resumen, faltantes


# ----------------------------------------------------------------------------
# Limpieza
# ----------------------------------------------------------------------------
def limpiar(df):
    # --- formato de CATEGORÍA (Activo / Activa) ---------------------------
    original = df["categoria"].copy()
    clave_cat = df["categoria"].map(lambda x: sin_tildes(x).strip().lower())
    df["categoria"] = clave_cat.map(CATEGORIAS_VALIDAS).fillna(df["categoria"])
    cambiadas = df[original != df["categoria"]]
    registrar(
        "Categoría escrita con distinto género ('Activa' / 'Activo')",
        "Unificar a 'Activo' (y 'Inactiva' a 'Inactivo' si aparece)",
        "Es la misma categoría; sin unificar se contaría como dos categorías distintas "
        "en los promedios y conteos por categoría del TP 3.",
        len(cambiadas), lista_ids(cambiadas["id_socio"]),
    )

    # --- registro duplicado (mismos datos; solo cambia el texto libre) ------
    # Se compara todo menos OBSERVACIONES: es texto libre y la copia puede variar
    # en una tilde o una palabra sin que sea otra persona.
    columnas_dato = [c for c in df.columns if c != "observaciones"]
    duplicadas = df[df.duplicated(subset=columnas_dato, keep="first")]
    registrar(
        "Fila repetida: mismo ID y mismos datos (solo difiere el texto libre de OBSERVACIONES)",
        "Eliminar la copia y conservar la primera aparición",
        "Es la misma carga repetida: mantenerla contaría dos veces al mismo socio. "
        "Un duplicado exacto (todas las columnas) no aparece porque la copia tiene "
        "una tilde distinta en OBSERVACIONES.",
        len(duplicadas), lista_ids(duplicadas["id_socio"]),
    )
    df = df.drop(index=duplicadas.index).copy()

    # --- misma persona cargada dos veces con distinto ID ---------
    # Criterio: mismo DNI + mismo email + mismo teléfono + misma fecha de alta.
    clave = ["dni", "email", "telefono", "fecha_alta"]
    misma_persona = df[df.duplicated(subset=clave, keep=False)]
    a_eliminar = []
    for _, grupo in misma_persona.groupby(clave, dropna=False):
        # Se conserva el registro con el nombre más completo (más largo).
        conservar = grupo.loc[grupo["socio"].str.len().idxmax()]
        a_eliminar += [i for i in grupo.index if i != conservar.name]
    eliminadas = df.loc[a_eliminar]
    registrar(
        "Misma persona con dos IDs distintos (mismo DNI, email, teléfono y alta; nombre abreviado)",
        "Eliminar el registro con nombre abreviado y conservar el de nombre completo",
        "Coinciden todos los datos de contacto y la fecha de alta: es un duplicado "
        "de persona, no dos socios. Conservar ambos duplicaría al socio en los conteos.",
        len(eliminadas), lista_ids(eliminadas["id_socio"]),
    )
    df = df.drop(index=a_eliminar).copy()

    # --- DNI repetido en personas distintas (solo se marca) ------
    dni_rep = df[df.duplicated(subset="dni", keep=False)]
    for _, fila in dni_rep.iterrows():
        marcar(fila["id_socio"], "DNI repetido con otro socio: verificar con el club")
    registrar(
        "Mismo DNI en socios con nombre, email, teléfono y alta distintos",
        "NO se elimina ni se corrige: se marca en la columna 'revisar'",
        "No hay evidencia para decidir cuál DNI es el correcto. Borrar uno sería "
        "inventar una conclusión; hay que confirmarlo con la administración.",
        len(dni_rep), lista_ids(dni_rep["id_socio"]),
    )

    # --- formato de ACTIVIDAD ------------------------------------
    original = df["actividad"].copy()
    clave_act = df["actividad"].map(lambda x: sin_tildes(x).strip().lower())
    df["actividad"] = clave_act.map(ACTIVIDADES_VALIDAS).fillna(df["actividad"])
    cambiadas = df[original != df["actividad"]]
    registrar(
        "Actividad escrita de formas distintas (padel, PADEL, PÁDEL, Futbol 5, Natacion...)",
        "Unificar a un solo nombre por actividad: Pádel, Fútbol 5, Natación",
        "Sin unificar, un mismo deporte se contaría como varias actividades en agrupaciones y gráficos.",
        len(cambiadas), lista_ids(cambiadas["id_socio"]),
    )

    # --- conversión de CUOTA a número ----------------------------
    df["cuota"] = df["cuota"].map(parsear_cuota)
    registrar(
        "CUOTA guardada como texto con símbolo y puntos ('$ 18.500')",
        "Convertir a número (float) quitando '$', espacios y separador de miles",
        "No se puede promediar ni sumar texto. Transformación de tipo de dato.",
        len(df), "todos",
    )

    # --- cuota negativa ------------------------------------------
    negativas = df[df["cuota"] < 0]
    for i, fila in negativas.iterrows():
        marcar(fila["id_socio"], f"Cuota con signo corregido (era {fila['cuota']:,.0f})")
    df.loc[negativas.index, "cuota"] = df.loc[negativas.index, "cuota"].abs()
    registrar(
        "Cuota negativa (-18.500)",
        "Pasar a valor absoluto (18.500)",
        "Una cuota no puede ser negativa. El monto es exactamente el de la cuota "
        "estándar y la planilla lo marca como 'Revisar signo': es un error de tipeo del signo.",
        len(negativas), lista_ids(negativas["id_socio"]),
    )

    # --- cuota atípica (error de carga) --------------------------
    positivas = df.loc[df["cuota"] > 0, "cuota"]
    umbral = FACTOR_CUOTA_ATIPICA * positivas.median()
    atipicas = df[df["cuota"] > umbral]
    for i, fila in atipicas.iterrows():
        valor_original = fila["cuota"]
        referencia = df[(df["categoria"] == fila["categoria"]) & (df["cuota"] > 0)
                        & (df["cuota"] <= umbral)]["cuota"].median()
        df.loc[i, "cuota"] = referencia
        marcar(fila["id_socio"],
               f"Cuota {valor_original:,.0f} reemplazada por {referencia:,.0f} "
               f"(mediana de la categoría {fila['categoria']}); confirmar con administración")
    registrar(
        f"Cuota atípica: supera {FACTOR_CUOTA_ATIPICA} veces la mediana de las cuotas positivas",
        "Reemplazar por la mediana de cuotas de su misma categoría (Cadete) y marcar en 'revisar'",
        "185.000 es 10 veces la cuota estándar y unas 15 veces la de otro Cadete. A diferencia de "
        "las cuotas 0 (exentos por estatuto, que son reales), acá no hay motivo que lo justifique: "
        "es un error de carga. SUPUESTO a confirmar con el club.",
        len(atipicas), lista_ids(atipicas["id_socio"]),
    )

    # --- cuotas en 0 (se conservan) ------------------------------
    ceros = df[df["cuota"] == 0]
    registrar(
        "Cuota $0 en socios Vitalicio y Honorario (valor atípico)",
        "Conservar sin cambios",
        "Estado EXENTO y observación 'Exento por estatuto' / 'Profesor': es un valor "
        "atípico REAL, no un error. Eliminarlo falsearía la composición de socios.",
        len(ceros), lista_ids(ceros["id_socio"]),
    )

    # --- fechas de alta -----------------------------------------
    df["fecha_alta"] = df["fecha_alta"].map(fecha_valida)
    inexistentes = df[df["fecha_alta"].isna()]
    for _, fila in inexistentes.iterrows():
        marcar(fila["id_socio"], "Fecha de alta inexistente (2026-02-30): se deja vacía")
    registrar(
        "Fecha de alta inexistente (30 de febrero)",
        "Convertir a fecha; la inválida queda vacía (NaT) y se marca en 'revisar'",
        "No hay forma de saber si fue el 28/02, el 02/03 u otra. Inventar una fecha "
        "falsearía la antigüedad. Sin imputar, el dato queda como faltante conocido.",
        len(inexistentes), lista_ids(inexistentes["id_socio"]),
    )

    futuras = df[df["fecha_alta"] > FECHA_CORTE]
    for _, fila in futuras.iterrows():
        marcar(fila["id_socio"], f"Fecha de alta posterior al corte ({FECHA_CORTE.date()}): se deja vacía")
    df.loc[futuras.index, "fecha_alta"] = pd.NaT
    registrar(
        f"Fecha de alta futura (posterior a la fecha de corte {FECHA_CORTE.date()})",
        "Dejar la fecha vacía (NaT) y marcar en 'revisar'; el socio se conserva",
        "Un alta no puede ser posterior al corte del padrón. El resto del registro "
        "(cuota PAGADA, Activo) es consistente, por eso se conserva el socio. SUPUESTO: la "
        "fecha de corte es una decisión del grupo; con la fecha de hoy esta alta ya sería pasada.",
        len(futuras), lista_ids(futuras["id_socio"]),
    )

    # --- inactivo con cuota vencida ------------------------------
    inc = df[(df["categoria"] == "Inactivo") & df["estado"].isin(["PENDIENTE", "VENCIDO"])]
    for _, fila in inc.iterrows():
        marcar(fila["id_socio"], "Socio dado de baja con cuota vencida: excluir de la morosidad de activos")
    registrar(
        "Socio dado de baja (Inactivo) que figura con cuota VENCIDA",
        "Conservar el registro y marcarlo en 'revisar'",
        "Es un dato histórico real, pero su deuda no corresponde a la morosidad de socios "
        "activos. Se decide en el TP 3 cómo tratarlo; borrarlo ahora perdería información.",
        len(inc), lista_ids(inc["id_socio"]),
    )

    # --- datos de contacto faltantes ----------------------------
    faltan_contacto = df[df["email"].isna() | df["telefono"].isna()]
    registrar(
        "Email o teléfono faltante (marcados con '—' en la planilla)",
        "Convertir '—' a vacío (NaN) y NO imputar",
        "Un email o teléfono no se puede deducir, y no se usa en el análisis de cuotas. "
        "Se deja como faltante real.",
        len(faltan_contacto), lista_ids(faltan_contacto["id_socio"]),
    )

    # --- Transformaciones adicionales -------------------------------------
    df["dni"] = df["dni"].map(a_texto_numerico)
    df["telefono"] = df["telefono"].map(a_texto_numerico)
    registrar(
        "DNI y teléfono pueden quedar como número (se pierden ceros, no se suman)",
        "Guardarlos como texto",
        "Son identificadores, no cantidades. Transformación de tipo de dato.",
        len(df), "todos",
    )

    def meses_antiguedad(f):
        if pd.isna(f):
            return pd.NA
        meses = (FECHA_CORTE.year - f.year) * 12 + (FECHA_CORTE.month - f.month)
        if FECHA_CORTE.day < f.day:
            meses -= 1
        return meses

    df["antiguedad_meses"] = df["fecha_alta"].map(meses_antiguedad).astype("Int64")
    df["anio_alta"] = df["fecha_alta"].dt.year.astype("Int64")
    registrar(
        "Faltan variables para analizar altas y antigüedad",
        f"Crear 'antiguedad_meses' (meses completos hasta {FECHA_CORTE.date()}) y 'anio_alta'",
        "Variables derivadas de la fecha de alta; necesarias para evolución de altas en el TP 3.",
        int(df["fecha_alta"].notna().sum()), "los que tienen fecha de alta válida",
    )

    df["revisar"] = df["id_socio"].map(lambda i: " | ".join(marcas.get(int(i), [])))
    df["revisar"] = df["revisar"].replace("", np.nan)
    return df[COLUMNAS_FINALES].sort_values("id_socio").reset_index(drop=True)


# ----------------------------------------------------------------------------
# Informe (Markdown)
# ----------------------------------------------------------------------------
def tabla_md(encabezados, filas):
    lineas = ["| " + " | ".join(encabezados) + " |",
              "|" + "|".join(["---"] * len(encabezados)) + "|"]
    for f in filas:
        lineas.append("| " + " | ".join(str(x).replace("|", "/") for x in f) + " |")
    return "\n".join(lineas)


def generar_informe(nombre_original, antes, despues, falt_antes, falt_despues, df_limpio):
    partes = []
    partes.append("# TP N° 2 – Limpieza y preparación de datos\n")
    partes.append("**Introducción al Análisis de Datos – UTN FRT – TUP (Plan 2024)** · Caso: Club Deportivo Cerro Alto\n")

    partes.append("## 1. Elección de herramienta\n")
    partes.append(
        "Se eligió **Python con pandas**. El dataset es chico (21 filas), por lo que Excel también "
        "alcanzaría, pero Python permite: (a) dejar cada decisión escrita en el código y en la "
        "bitácora, (b) volver a ejecutar toda la limpieza sobre el original con un comando y obtener "
        "el mismo resultado, y (c) repetir la inspección antes/después de forma idéntica. Eso da "
        "trazabilidad, que es lo que pide el TP, y deja el dataset listo para el TP 3 (pandas, SQL y gráficos).\n"
    )
    partes.append(f"Archivo original: `datos/{nombre_original}` (no se modifica). "
                  f"Fecha de corte del padrón (supuesto): **{FECHA_CORTE.date()}**.\n")

    partes.append("## 2. Bitácora de limpieza\n")
    partes.append(tabla_md(
        ["Paso", "Problema", "Decisión", "Razón", "Filas", "IDs"],
        [[b["paso"], b["problema"], b["decision"], b["razon"], b["filas_afectadas"], b["ids_afectados"]]
         for b in bitacora],
    ) + "\n")

    partes.append("## 3. Validación final (antes vs. después)\n")
    partes.append(tabla_md(
        ["Control", "Antes", "Después"],
        [[k, antes[k], despues[k]] for k in antes],
    ) + "\n")

    partes.append(
        "Los controles que no llegan a cero son **decisiones, no errores sin tratar**: el DNI repetido "
        "entre dos socios distintos y el socio inactivo con cuota vencida se marcan en `revisar` "
        "para confirmarlos con el club, porque no hay evidencia para corregirlos.\n"
    )
    partes.append("### Valores faltantes por columna (columnas originales; '—' cuenta como faltante)\n")
    partes.append(tabla_md(
        ["Columna", "Antes", "Después"],
        [[c, int(falt_antes[c]), int(falt_despues[c])] for c in falt_antes.index],
    ) + "\n")
    partes.append(
        "Los faltantes que quedan son esperables: email, teléfono y observaciones no se imputan; "
        "las dos fechas de alta inválidas (106 y 119) quedan vacías a propósito, por eso fecha_alta "
        "pasa de 0 a 2 faltantes.\n"
    )

    partes.append("### Variantes de ACTIVIDAD luego de la limpieza\n")
    partes.append(", ".join(sorted(df_limpio["actividad"].unique())) + "\n")

    partes.append("## 4. Resultado\n")
    partes.append(
        f"El dataset limpio tiene **{len(df_limpio)} socios** (el original tenía {antes['Filas']} filas). "
        "Los problemas de duplicados, formato, signo y valor erróneo quedaron resueltos. Quedan "
        "**marcados en la columna `revisar`** (no resueltos, a propósito) los casos que requieren "
        "confirmación del club: DNI repetido entre dos socios distintos, fechas de alta inválidas, "
        "cuota reemplazada y socio dado de baja con deuda.\n"
    )
    return "\n".join(partes)


# ----------------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------------
def main():
    ruta = buscar_original()
    print(f"Leyendo: {ruta.name}")
    df = normalizar_vacios(leer_original(ruta))

    antes, falt_antes = inspeccionar(df)
    limpio = limpiar(df)
    despues, falt_despues = inspeccionar(limpio)

    informe = generar_informe(ruta.name, antes, despues, falt_antes, falt_despues, limpio)
    SALIDA_INFORME.write_text(informe, encoding="utf-8")

    bitacora_df = pd.DataFrame(bitacora)
    with pd.ExcelWriter(SALIDA_XLSX, engine="openpyxl") as writer:
        limpio.to_excel(writer, sheet_name="socios_limpio", index=False)
        bitacora_df.to_excel(writer, sheet_name="bitacora", index=False)

    print(f"Filas: {antes['Filas']} -> {len(limpio)}")
    print(f"Dataset limpio: {SALIDA_XLSX}")
    print(f"Informe:        {SALIDA_INFORME}")


if __name__ == "__main__":
    main()