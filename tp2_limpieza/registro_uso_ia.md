# Registro de uso de IA – TP N° 2

Ciclo aplicado: problema → propuesta → análisis → verificación → corrección.

## 1. Problema
Limpiar el padrón de socios y cuotas de Cerro Alto (21 filas) con Python/pandas,
dejando una bitácora de cada decisión y una validación antes/después.

## 2. Propuesta de la IA
Claude propuso un script de limpieza (`limpieza_datos.py`). La primera versión se
armó a partir de una transcripción del padrón en PDF, no del Excel original.

## 3. Análisis
Revisé cada paso del script y la razón de cada decisión de la bitácora
(duplicados, formato de actividad, cuota negativa, cuota atípica, fechas inválidas,
DNI repetido, socio inactivo con deuda).

## 4. Verificación
Ejecuté el script sobre el Excel original de la cátedra
(`Registro_Socios_Cuotas_Cerro_Alto_Para_Alumnos.xlsx`). Resultado: 21 → 19 filas.
Comparé contra el original los socios 101, 104, 105, 106, 108, 110 y 119.

## 5. Corrección
El original difería de la transcripción en dos puntos, y la primera versión no
los resolvía bien:
- La columna CAT. mezclaba "Activo" y "Activa" (8 filas). Se agregó un paso que
  unifica la categoría.
- La fila repetida del socio 101 no era un duplicado exacto: difería en
  "Activa"/"Activo" y en una tilde de OBSERVACIONES. Se cambió el criterio para
  detectar duplicados ignorando OBSERVACIONES, y se registró con su razón correcta.
Tras las correcciones, la bitácora quedó en 15 pasos y el resultado se mantuvo en 19 socios.

## Decisiones propias (supuestos que puedo defender)
- Fecha de corte del padrón: 2026-06-30, para que el alta del socio 119 (2026-09-30)
  resulte posterior al corte, como indica la observación de la planilla.
- Cuota de 185.000 (socio 105): se reemplazó por 12.000, la cuota de la categoría
  Cadete. A confirmar con el club.
- Los socios con cuota $0 (Vitalicio y Honorario) se conservan: son exentos por estatuto.
- El DNI repetido entre los socios 108 y 119 se marca y no se corrige.