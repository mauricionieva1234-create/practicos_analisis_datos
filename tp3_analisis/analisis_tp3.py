"""
UTN FRT - Tecnicatura Universitaria en Programación
Introducción al Análisis de Datos - TP N° 3: Análisis y visualización
Caso integrador: Club Deportivo Cerro Alto

Qué hace este script:
  1. Lee el dataset limpio del TP 2 (datos/Registro_Socios_LIMPIO.xlsx, hoja socios_limpio).
  2. Responde 4 preguntas de negocio con SQL (SQLite, consultas.sql) y/o pandas.
  3. Verifica cada resultado calculándolo por el otro camino (SQL vs. pandas).
  4. Genera los gráficos de las preguntas 1 y 2.
  5. Escribe el informe con consultas, resultados, gráficos e interpretaciones.

Genera:
  - tp3_analisis/graficos/p1_socios_por_actividad.png
  - tp3_analisis/graficos/p2_estado_cuotas.png
  - tp3_analisis/resultados_tp3.xlsx
  - tp3_analisis/informe_tp3.md

Uso (desde la raíz del repo):
    python -m pip install pandas openpyxl matplotlib
    python tp3_analisis/analisis_tp3.py
"""

from pathlib import Path
import sqlite3

import matplotlib
matplotlib.use("Agg")  # genera las imágenes sin abrir ventanas
import matplotlib.pyplot as plt
import pandas as pd

# ----------------------------------------------------------------------------
# Configuración
# ----------------------------------------------------------------------------
CARPETA = Path(__file__).resolve().parent
RAIZ = CARPETA.parent
ENTRADA = RAIZ / "datos" / "Registro_Socios_LIMPIO.xlsx"
ARCHIVO_SQL = CARPETA / "consultas.sql"
CARPETA_GRAFICOS = CARPETA / "graficos"
SALIDA_INFORME = CARPETA / "informe_tp3.md"
SALIDA_RESULTADOS = CARPETA / "resultados_tp3.xlsx"

ORDEN_ESTADOS = ["PAGADO", "PENDIENTE", "VENCIDO"]
COLOR_BARRAS = "#2f6f8f"

verificaciones = []   # (descripción, True/False)


# ----------------------------------------------------------------------------
# Utilidades de formato
# ----------------------------------------------------------------------------
def pesos(valor):
    """18500 -> '$ 18.500'"""
    return "$ " + f"{valor:,.0f}".replace(",", ".")


def porcentaje(valor):
    """75.0 -> '75,0 %'"""
    return f"{valor:.1f}".replace(".", ",") + " %"


def tabla_md(df):
    """DataFrame -> tabla Markdown (sin depender de librerías extra)."""
    cols = list(df.columns)
    lineas = ["| " + " | ".join(str(c) for c in cols) + " |",
              "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, fila in df.iterrows():
        lineas.append("| " + " | ".join(str(v) for v in fila) + " |")
    return "\n".join(lineas)


def lista_texto(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " y " + items[-1]


# ----------------------------------------------------------------------------
# Datos y SQL
# ----------------------------------------------------------------------------
def cargar_socios():
    df = pd.read_excel(
        ENTRADA, sheet_name="socios_limpio", dtype={"dni": str, "telefono": str}
    )
    df["fecha_alta"] = pd.to_datetime(df["fecha_alta"])
    df["anio_alta"] = df["anio_alta"].astype("Int64")
    return df


def crear_bd(df):
    """Carga el dataset en una base SQLite en memoria (tabla 'socios')."""
    df_sql = df.copy()
    df_sql["fecha_alta"] = df_sql["fecha_alta"].dt.strftime("%Y-%m-%d")
    df_sql["anio_alta"] = df_sql["anio_alta"].astype("float")
    df_sql["antiguedad_meses"] = df_sql["antiguedad_meses"].astype("float")
    con = sqlite3.connect(":memory:")
    df_sql.to_sql("socios", con, index=False)
    return con


def cargar_consultas(ruta):
    """Lee consultas.sql: cada consulta empieza con una línea '-- name: <nombre>'."""
    consultas, nombre, lineas = {}, None, []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("-- name:"):
            if nombre:
                consultas[nombre] = "\n".join(lineas).strip()
            nombre, lineas = linea.split(":", 1)[1].strip(), []
        elif nombre:
            lineas.append(linea)
    if nombre:
        consultas[nombre] = "\n".join(lineas).strip()
    return consultas


def verificar(descripcion, condicion):
    verificaciones.append((descripcion, bool(condicion)))


# ----------------------------------------------------------------------------
# Gráficos
# ----------------------------------------------------------------------------
def grafico_actividades(r1, total):
    datos = r1.sort_values("socios_vigentes", ascending=True)  # el mayor queda arriba
    fig, ax = plt.subplots(figsize=(7, 4))
    barras = ax.barh(datos["actividad"], datos["socios_vigentes"], color=COLOR_BARRAS)
    for barra, valor in zip(barras, datos["socios_vigentes"]):
        ax.text(valor + 0.1, barra.get_y() + barra.get_height() / 2, str(valor),
                va="center")
    ax.set_title(f"Socios vigentes por actividad (n = {total})")
    ax.set_xlabel("Cantidad de socios")
    ax.set_xlim(0, datos["socios_vigentes"].max() + 1)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    fig.tight_layout()
    ruta = CARPETA_GRAFICOS / "p1_socios_por_actividad.png"
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return ruta


def grafico_estados(conteo, n_obligados):
    fig, ax = plt.subplots(figsize=(7, 4))
    barras = ax.bar(conteo.index, conteo.values, color=COLOR_BARRAS)
    for barra, valor in zip(barras, conteo.values):
        pct = valor / n_obligados * 100
        ax.text(barra.get_x() + barra.get_width() / 2, valor + 0.2,
                f"{valor} ({porcentaje(pct)})", ha="center")
    ax.set_title(f"Estado de cuota de los socios obligados a pagar (n = {n_obligados})")
    ax.set_ylabel("Cantidad de socios")
    ax.set_ylim(0, conteo.max() + 2)
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    fig.tight_layout()
    ruta = CARPETA_GRAFICOS / "p2_estado_cuotas.png"
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return ruta


# ----------------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------------
def main():
    CARPETA_GRAFICOS.mkdir(exist_ok=True)
    df = cargar_socios()
    con = crear_bd(df)
    sql = cargar_consultas(ARCHIVO_SQL)

    # ------------------------------------------------------------------
    # P1. Socios vigentes por actividad  (SQL; verificación con pandas)
    # ------------------------------------------------------------------
    r1 = pd.read_sql_query(sql["q1_socios_por_actividad"], con)
    vigentes = df[df["categoria"] != "Inactivo"]
    por_pandas = vigentes.groupby("actividad").size().to_dict()
    verificar("P1: el conteo por actividad de SQL coincide con pandas",
              dict(zip(r1["actividad"], r1["socios_vigentes"])) == por_pandas)
    verificar("P1: la suma por actividad es igual al total de socios vigentes",
              r1["socios_vigentes"].sum() == len(vigentes))
    total_vigentes = int(r1["socios_vigentes"].sum())
    grafico1 = grafico_actividades(r1, total_vigentes)

    # ------------------------------------------------------------------
    # P2. Cuota al día entre los socios obligados  (pandas; verificación con SQL)
    # ------------------------------------------------------------------
    obligados = df[(df["categoria"] != "Inactivo") & (df["estado"] != "EXENTO")]
    n_obligados = len(obligados)
    conteo = obligados["estado"].value_counts().reindex(ORDEN_ESTADOS, fill_value=0)
    monto = obligados.groupby("estado")["cuota"].sum().reindex(ORDEN_ESTADOS, fill_value=0)
    r2_sql = pd.read_sql_query(sql["q2_estado_obligados"], con).set_index("estado")
    verificar("P2: conteo de estados de pandas coincide con SQL",
              all(int(r2_sql["socios"].get(e, 0)) == int(conteo[e]) for e in ORDEN_ESTADOS))
    verificar("P2: montos por estado de pandas coinciden con SQL",
              all(int(r2_sql["monto"].get(e, 0)) == int(monto[e]) for e in ORDEN_ESTADOS))
    pagados = int(conteo["PAGADO"])
    pendientes = int(conteo["PENDIENTE"])
    vencidos = int(conteo["VENCIDO"])
    pct_al_dia = pagados / n_obligados * 100
    monto_total = int(monto.sum())
    monto_pendiente = int(monto["PENDIENTE"] + monto["VENCIDO"])
    pct_monto_pend = monto_pendiente / monto_total * 100
    # Sensibilidad: qué pasa si se incluyen los dados de baja con cuota vencida
    inactivos_con_deuda = df[(df["categoria"] == "Inactivo")
                             & df["estado"].isin(["PENDIENTE", "VENCIDO"])]
    pct_con_inactivos = pagados / (n_obligados + len(inactivos_con_deuda)) * 100
    deudores = obligados[obligados["estado"].isin(["PENDIENTE", "VENCIDO"])].copy()
    deudores["contacto"] = deudores.apply(
        lambda f: ("email y teléfono" if pd.notna(f["email"]) and pd.notna(f["telefono"])
                   else "solo teléfono" if pd.notna(f["telefono"])
                   else "solo email" if pd.notna(f["email"]) else "sin contacto"),
        axis=1,
    )
    tabla_deudores = deudores[["id_socio", "socio", "actividad", "estado", "cuota", "contacto"]].copy()
    tabla_deudores["cuota"] = tabla_deudores["cuota"].map(pesos)
    grafico2 = grafico_estados(conteo, n_obligados)
    r2 = pd.DataFrame({
        "estado": ORDEN_ESTADOS,
        "socios": [int(conteo[e]) for e in ORDEN_ESTADOS],
        "porcentaje": [porcentaje(conteo[e] / n_obligados * 100) for e in ORDEN_ESTADOS],
        "monto": [pesos(monto[e]) for e in ORDEN_ESTADOS],
    })

    # ------------------------------------------------------------------
    # P3. Cuota promedio por categoría  (SQL; verificación con pandas)
    # ------------------------------------------------------------------
    r3 = pd.read_sql_query(sql["q3_cuota_por_categoria"], con)
    prom_pandas = df.groupby("categoria")["cuota"].mean().round(0).to_dict()
    verificar("P3: los promedios por categoría de SQL coinciden con pandas",
              all(abs(prom_pandas[c] - p) < 0.5 for c, p in zip(r3["categoria"], r3["cuota_promedio"])))
    verificar("P3: la suma de socios por categoría es igual al total de socios",
              r3["socios"].sum() == len(df))
    cuota_estandar = int(df.loc[df["cuota"] > 0, "cuota"].median())
    activos_no_estandar = df[(df["categoria"] == "Activo") & (df["cuota"] != cuota_estandar)]
    n_imputadas = int(df["revisar"].fillna("").str.contains("reemplazada").sum())
    prom_activo = float(r3.loc[r3["categoria"] == "Activo", "cuota_promedio"].iloc[0])
    r3_vista = r3.copy()
    for col in ("cuota_promedio", "cuota_minima", "cuota_maxima"):
        r3_vista[col] = r3_vista[col].map(pesos)

    # ------------------------------------------------------------------
    # P4. Altas por año  (pandas; verificación con SQL)
    # ------------------------------------------------------------------
    con_fecha = df.dropna(subset=["anio_alta"])
    r4 = (con_fecha.groupby("anio_alta").size().reset_index(name="altas")
          .rename(columns={"anio_alta": "anio"}))
    r4["anio"] = r4["anio"].astype(int)
    r4_sql = pd.read_sql_query(sql["q4_altas_por_anio"], con)
    verificar("P4: las altas por año de pandas coinciden con SQL",
              r4["altas"].tolist() == r4_sql["altas"].tolist()
              and r4["anio"].tolist() == r4_sql["anio_alta"].astype(int).tolist())
    sin_fecha = df[df["fecha_alta"].isna()]
    verificar("P4: altas con fecha + socios sin fecha válida = total de socios",
              r4["altas"].sum() + len(sin_fecha) == len(df))
    anio_top = r4.loc[r4["altas"].idxmax()]
    ultima_alta = df["fecha_alta"].max()
    r4_vista = r4.copy()
    r4_vista.loc[len(r4_vista)] = ["sin fecha válida", len(sin_fecha)]

    # ------------------------------------------------------------------
    # Resultados en Excel
    # ------------------------------------------------------------------
    with pd.ExcelWriter(SALIDA_RESULTADOS, engine="openpyxl") as writer:
        r1.to_excel(writer, sheet_name="p1_actividades", index=False)
        r2.to_excel(writer, sheet_name="p2_estado_cuotas", index=False)
        r3.to_excel(writer, sheet_name="p3_cuota_categoria", index=False)
        r4_vista.to_excel(writer, sheet_name="p4_altas_anio", index=False)

    # ------------------------------------------------------------------
    # Textos de interpretación (con los números calculados)
    # ------------------------------------------------------------------
    top1 = r1.iloc[0]
    minimos = r1[r1["socios_vigentes"] == r1["socios_vigentes"].min()]["actividad"].tolist()
    inter1 = (
        f"{top1['actividad']} concentra {int(top1['socios_vigentes'])} de los {total_vigentes} socios "
        f"vigentes ({porcentaje(top1['socios_vigentes'] / total_vigentes * 100)}), y "
        f"{lista_texto(minimos)} tiene{'n' if len(minimos) > 1 else ''} un solo socio cada una. "
        f"La comisión puede usar esto para decidir dónde reforzar la capacidad (horarios y canchas de "
        f"{top1['actividad']}) y qué actividades de baja participación conviene promover o evaluar si "
        f"se justifica mantenerlas. Con tan pocos socios, una sola alta o baja cambia el ranking."
    )
    detalle_deudores = "; ".join(
        f"{f['socio']} ({f['actividad']}, {f['contacto']})" for _, f in deudores.iterrows())
    imputadas_obligados = int(obligados["revisar"].fillna("").str.contains("reemplazada").sum())
    aviso_monto = (
        f" Los montos incluyen {imputadas_obligados} cuota corregida en el TP 2 (supuesto a confirmar)."
        if imputadas_obligados else ""
    )
    inter2 = (
        f"{pagados} de {n_obligados} socios obligados tienen la cuota al día ({porcentaje(pct_al_dia)}); "
        f"{pendientes} figuran PENDIENTE y {vencidos} VENCIDO, lo que equivale a {pesos(monto_pendiente)} "
        f"sin cobrar ({porcentaje(pct_monto_pend)} de {pesos(monto_total)} facturados a socios obligados). "
        f"La comisión puede contactar a esos socios: {detalle_deudores}. "
        f"Si se incluyera al socio dado de baja con cuota vencida, el porcentaje al día bajaría a "
        f"{porcentaje(pct_con_inactivos)}: por eso se lo excluye, ya que su deuda no es morosidad de un "
        f"socio activo. PENDIENTE no necesariamente significa mora: conviene confirmar con la "
        f"administración si esas cuotas ya vencieron." + aviso_monto
    )
    inter3 = (
        f"La cuota estándar es {pesos(cuota_estandar)}. El promedio de la categoría Activo "
        f"({pesos(prom_activo)}) queda por encima porque incluye "
        f"{'socios' if len(activos_no_estandar) != 1 else 'un socio'} con otra cuota "
        f"({lista_texto([f'{f.socio} de {f.actividad}: {pesos(f.cuota)}' for f in activos_no_estandar.itertuples()])}). "
        f"Los socios Vitalicio y Honorario tienen cuota $ 0 por estatuto, así que no aportan ingreso "
        f"mensual. La comisión puede revisar si las diferencias de cuota entre actividades responden a "
        f"una política definida y cuántos socios exentos hay. Atención: el valor de la categoría Cadete "
        f"incluye {n_imputadas} cuota corregida en el TP 2 (supuesto a confirmar con el club)."
    )
    inter4 = (
        f"{int(anio_top['altas'])} de las {int(r4['altas'].sum())} altas con fecha válida son de "
        f"{int(anio_top['anio'])}, y la última alta registrada es del {ultima_alta.strftime('%d/%m/%Y')}: "
        f"no hay altas con fecha válida posteriores. Hay {len(sin_fecha)} socios sin fecha de alta "
        f"válida ({', '.join(str(i) for i in sin_fecha['id_socio'])}) que podrían ser altas recientes. "
        f"La comisión puede preguntarse si el club dejó de sumar socios o si el padrón no se actualizó, "
        f"y regularizar esas fechas antes de sacar conclusiones sobre el crecimiento."
    )

    # ------------------------------------------------------------------
    # Informe
    # ------------------------------------------------------------------
    n_ok = sum(1 for _, ok in verificaciones if ok)
    estado_verif = "\n".join(f"- {'OK' if ok else 'FALLÓ'}: {d}" for d, ok in verificaciones)
    partes = [
        "# TP N° 3 – Análisis y visualización\n",
        "**Introducción al Análisis de Datos – UTN FRT – TUP (Plan 2024)** · Caso: Club Deportivo Cerro Alto\n",
        "## Herramienta y datos\n",
        "Python con pandas y matplotlib; las consultas SQL se ejecutan sobre SQLite (en memoria) "
        "con el archivo `consultas.sql`. Se parte del dataset limpio del TP 2 "
        f"(`datos/Registro_Socios_LIMPIO.xlsx`, {len(df)} socios).\n",
        "**Definiciones usadas**\n",
        "- *Socio vigente*: categoría distinta de Inactivo (no fue dado de baja). Incluye Activo, Cadete, "
        "Vitalicio y Honorario.\n"
        "- *Socio obligado*: vigente y con estado distinto de EXENTO (debe pagar cuota).\n"
        "- *Cuota al día*: estado PAGADO.\n",
        "**Advertencia:** con solo 19 socios, los porcentajes dan saltos grandes (un socio equivale a "
        "más de 5 puntos). Las conclusiones son descriptivas del padrón, no tendencias estadísticas.\n",
        # ---- P1
        "## Pregunta 1 – ¿Cuántos socios vigentes hay y cómo se reparten por actividad?\n",
        "**Método:** consulta SQL (conteo agrupado por actividad).\n",
        "```sql\n" + sql["q1_socios_por_actividad"] + "\n```\n",
        tabla_md(r1) + "\n",
        f"![Socios vigentes por actividad](graficos/{grafico1.name})\n",
        "**Elección del gráfico:** es una comparación de cantidades entre categorías nominales "
        "(actividades), por eso se usan barras horizontales ordenadas de mayor a menor, con el valor "
        "escrito en cada barra y el eje desde cero. Las barras horizontales dejan leer los nombres sin "
        "rotarlos y el orden permite ver el ranking de un vistazo. Una torta se descarta: con 6 "
        "categorías y valores chicos, comparar ángulos es más difícil que comparar largos. "
        "(Contrastá este argumento con tus apuntes de la Unidad 5.)\n",
        "**Interpretación:** " + inter1 + "\n",
        # ---- P2
        "## Pregunta 2 – ¿Qué porcentaje de los socios obligados a pagar tiene la cuota al día?\n",
        "**Método:** pandas (filtro de socios obligados y conteo por estado); verificado con SQL.\n",
        "```python\nobligados = df[(df['categoria'] != 'Inactivo') & (df['estado'] != 'EXENTO')]\n"
        "conteo = obligados['estado'].value_counts()\n```\n",
        "```sql\n" + sql["q2_estado_obligados"] + "\n```\n",
        tabla_md(r2) + "\n",
        "Socios con cuota sin pagar:\n",
        tabla_md(tabla_deudores) + "\n",
        f"![Estado de cuota de los socios obligados](graficos/{grafico2.name})\n",
        "**Elección del gráfico:** se compara la cantidad de socios en cada estado de pago, que es una "
        "variable categórica con pocas categorías. Barras verticales con la cantidad y el porcentaje "
        "sobre cada una, eje desde cero y los tres estados posibles (aunque VENCIDO sea 0, para que "
        "se vea que no hay). Se evita la torta porque con un estado en cero y dos con valores muy "
        "distintos aporta menos que las barras.\n",
        "**Interpretación:** " + inter2 + "\n",
        # ---- P3
        "## Pregunta 3 – ¿Cuál es la cuota promedio por categoría de socio?\n",
        "**Método:** consulta SQL (promedio agrupado por categoría); verificada con pandas.\n",
        "```sql\n" + sql["q3_cuota_por_categoria"] + "\n```\n",
        tabla_md(r3_vista) + "\n",
        "**Interpretación:** " + inter3 + "\n",
        # ---- P4
        "## Pregunta 4 – ¿Cómo evolucionaron las altas de socios por año?\n",
        "**Método:** pandas (conteo por año de alta); verificado con SQL.\n",
        "```python\ncon_fecha = df.dropna(subset=['anio_alta'])\n"
        "altas = con_fecha.groupby('anio_alta').size()\n```\n",
        tabla_md(r4_vista) + "\n",
        "**Interpretación:** " + inter4 + "\n",
        # ---- verificaciones
        "## Verificaciones realizadas\n",
        f"Cada resultado se calculó por dos caminos (SQL y pandas) y se compararon: {n_ok} de "
        f"{len(verificaciones)} verificaciones coinciden.\n",
        estado_verif + "\n",
        "## Uso de inteligencia artificial\n",
        "El registro del proceso (problema → propuesta → análisis → verificación → corrección) "
        "está en `registro_uso_ia_tp3.md`.\n",
    ]
    SALIDA_INFORME.write_text("\n".join(partes), encoding="utf-8")

    print(f"Socios: {len(df)} | vigentes: {total_vigentes} | obligados: {n_obligados}")
    print(f"Verificaciones: {n_ok}/{len(verificaciones)} OK")
    for descripcion, ok in verificaciones:
        print(("  OK     " if ok else "  FALLÓ  ") + descripcion)
    print(f"Gráficos: {CARPETA_GRAFICOS}")
    print(f"Informe:  {SALIDA_INFORME}")


if __name__ == "__main__":
    main()