# TP N° 2 – Limpieza y preparación de datos

**Introducción al Análisis de Datos – UTN FRT – TUP (Plan 2024)** · Caso: Club Deportivo Cerro Alto

## 1. Elección de herramienta

Se eligió **Python con pandas**. El dataset es chico (21 filas), por lo que Excel también alcanzaría, pero Python permite: (a) dejar cada decisión escrita en el código y en la bitácora, (b) volver a ejecutar toda la limpieza sobre el original con un comando y obtener el mismo resultado, y (c) repetir la inspección antes/después de forma idéntica. Eso da trazabilidad, que es lo que pide el TP, y deja el dataset listo para el TP 3 (pandas, SQL y gráficos).

Archivo original: `datos/Registro_Socios_Cuotas_Cerro_Alto_Para_Alumnos.xlsx` (no se modifica). Fecha de corte del padrón (supuesto): **2026-06-30**.

## 2. Bitácora de limpieza

| Paso | Problema | Decisión | Razón | Filas | IDs |
|---|---|---|---|---|---|
| 1 | Categoría escrita con distinto género ('Activa' / 'Activo') | Unificar a 'Activo' (y 'Inactiva' a 'Inactivo' si aparece) | Es la misma categoría; sin unificar se contaría como dos categorías distintas en los promedios y conteos por categoría del TP 3. | 8 | 101, 104, 109, 110, 112, 115, 117, 118 |
| 2 | Fila repetida: mismo ID y mismos datos (solo difiere el texto libre de OBSERVACIONES) | Eliminar la copia y conservar la primera aparición | Es la misma carga repetida: mantenerla contaría dos veces al mismo socio. Un duplicado exacto (todas las columnas) no aparece porque la copia tiene una tilde distinta en OBSERVACIONES. | 1 | 101 |
| 3 | Misma persona con dos IDs distintos (mismo DNI, email, teléfono y alta; nombre abreviado) | Eliminar el registro con nombre abreviado y conservar el de nombre completo | Coinciden todos los datos de contacto y la fecha de alta: es un duplicado de persona, no dos socios. Conservar ambos duplicaría al socio en los conteos. | 1 | 110 |
| 4 | Mismo DNI en socios con nombre, email, teléfono y alta distintos | NO se elimina ni se corrige: se marca en la columna 'revisar' | No hay evidencia para decidir cuál DNI es el correcto. Borrar uno sería inventar una conclusión; hay que confirmarlo con la administración. | 2 | 108, 119 |
| 5 | Actividad escrita de formas distintas (padel, PADEL, PÁDEL, Futbol 5, Natacion...) | Unificar a un solo nombre por actividad: Pádel, Fútbol 5, Natación | Sin unificar, un mismo deporte se contaría como varias actividades en agrupaciones y gráficos. | 6 | 102, 104, 105, 108, 116, 117 |
| 6 | CUOTA guardada como texto con símbolo y puntos ('$ 18.500') | Convertir a número (float) quitando '$', espacios y separador de miles | No se puede promediar ni sumar texto. Transformación de tipo de dato. | 19 | todos |
| 7 | Cuota negativa (-18.500) | Pasar a valor absoluto (18.500) | Una cuota no puede ser negativa. El monto es exactamente el de la cuota estándar y la planilla lo marca como 'Revisar signo': es un error de tipeo del signo. | 1 | 104 |
| 8 | Cuota atípica: supera 5 veces la mediana de las cuotas positivas | Reemplazar por la mediana de cuotas de su misma categoría (Cadete) y marcar en 'revisar' | 185.000 es 10 veces la cuota estándar y unas 15 veces la de otro Cadete. A diferencia de las cuotas 0 (exentos por estatuto, que son reales), acá no hay motivo que lo justifique: es un error de carga. SUPUESTO a confirmar con el club. | 1 | 105 |
| 9 | Cuota $0 en socios Vitalicio y Honorario (valor atípico) | Conservar sin cambios | Estado EXENTO y observación 'Exento por estatuto' / 'Profesor': es un valor atípico REAL, no un error. Eliminarlo falsearía la composición de socios. | 2 | 107, 120 |
| 10 | Fecha de alta inexistente (30 de febrero) | Convertir a fecha; la inválida queda vacía (NaT) y se marca en 'revisar' | No hay forma de saber si fue el 28/02, el 02/03 u otra. Inventar una fecha falsearía la antigüedad. Sin imputar, el dato queda como faltante conocido. | 1 | 106 |
| 11 | Fecha de alta futura (posterior a la fecha de corte 2026-06-30) | Dejar la fecha vacía (NaT) y marcar en 'revisar'; el socio se conserva | Un alta no puede ser posterior al corte del padrón. El resto del registro (cuota PAGADA, Activo) es consistente, por eso se conserva el socio. SUPUESTO: la fecha de corte es una decisión del grupo; con la fecha de hoy esta alta ya sería pasada. | 1 | 119 |
| 12 | Socio dado de baja (Inactivo) que figura con cuota VENCIDA | Conservar el registro y marcarlo en 'revisar' | Es un dato histórico real, pero su deuda no corresponde a la morosidad de socios activos. Se decide en el TP 3 cómo tratarlo; borrarlo ahora perdería información. | 1 | 111 |
| 13 | Email o teléfono faltante (marcados con '—' en la planilla) | Convertir '—' a vacío (NaN) y NO imputar | Un email o teléfono no se puede deducir, y no se usa en el análisis de cuotas. Se deja como faltante real. | 4 | 102, 103, 111, 115 |
| 14 | DNI y teléfono pueden quedar como número (se pierden ceros, no se suman) | Guardarlos como texto | Son identificadores, no cantidades. Transformación de tipo de dato. | 19 | todos |
| 15 | Faltan variables para analizar altas y antigüedad | Crear 'antiguedad_meses' (meses completos hasta 2026-06-30) y 'anio_alta' | Variables derivadas de la fecha de alta; necesarias para evolución de altas en el TP 3. | 17 | los que tienen fecha de alta válida |

## 3. Validación final (antes vs. después)

| Control | Antes | Después |
|---|---|---|
| Filas | 21 | 19 |
| Filas duplicadas (mismo DNI, email, teléfono y alta) | 2 | 0 |
| ID de socio repetidos | 1 | 0 |
| Filas con DNI repetido | 6 | 2 |
| Variantes distintas de ACTIVIDAD | 12 | 6 |
| Variantes distintas de CATEGORÍA (CAT.) | 6 | 5 |
| Cuotas negativas | 1 | 0 |
| Cuotas atípicas (> 5 x mediana) | 1 | 0 |
| Fechas de alta inexistentes (ej. 30 de febrero) | 1 | 0 |
| Fechas de alta posteriores al corte | 1 | 0 |
| Socios inactivos con cuota pendiente/vencida | 1 | 1 |

Los controles que no llegan a cero son **decisiones, no errores sin tratar**: el DNI repetido entre dos socios distintos y el socio inactivo con cuota vencida se marcan en `revisar` para confirmarlos con el club, porque no hay evidencia para corregirlos.

### Valores faltantes por columna (columnas originales; '—' cuenta como faltante)

| Columna | Antes | Después |
|---|---|---|
| id_socio | 0 | 0 |
| socio | 0 | 0 |
| dni | 0 | 0 |
| fecha_alta | 0 | 2 |
| actividad | 0 | 0 |
| categoria | 0 | 0 |
| cuota | 0 | 0 |
| estado | 0 | 0 |
| email | 1 | 1 |
| telefono | 3 | 3 |
| observaciones | 10 | 10 |

Los faltantes que quedan son esperables: email, teléfono y observaciones no se imputan; las dos fechas de alta inválidas (106 y 119) quedan vacías a propósito, por eso fecha_alta pasa de 0 a 2 faltantes.

### Variantes de ACTIVIDAD luego de la limpieza

Básquet, Fútbol 5, Gimnasio, Natación, Pádel, Tenis

## 4. Resultado

El dataset limpio tiene **19 socios** (el original tenía 21 filas). Los problemas de duplicados, formato, signo y valor erróneo quedaron resueltos. Quedan **marcados en la columna `revisar`** (no resueltos, a propósito) los casos que requieren confirmación del club: DNI repetido entre dos socios distintos, fechas de alta inválidas, cuota reemplazada y socio dado de baja con deuda.
