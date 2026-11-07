# Introducción al Análisis de Datos – Caso Cerro Alto

UTN FRT – Tecnicatura Universitaria en Programación.

## Estructura

| Carpeta / archivo | Contenido |
|---|---|
| `datos/Registro_Socios_Cuotas_Cerro_Alto_Para_Alumnos.xlsx` | Padrón original de la cátedra (sin modificar) |
| `datos/Registro_Socios_LIMPIO.xlsx` | Dataset limpio y bitácora (generado por el script del TP 2) |
| `tp2_limpieza/limpieza_datos.py` | Script de limpieza (TP N° 2) |
| `tp2_limpieza/informe_tp2.md` | Herramienta, bitácora y validación final |
| `tp2_limpieza/registro_uso_ia.md` | Registro del uso de IA del TP 2 |
| `tp3_analisis/analisis_tp3.py` | Script de análisis y gráficos (TP N° 3) |
| `tp3_analisis/consultas.sql` | Consultas SQL |
| `tp3_analisis/informe_tp3.md` | Preguntas, resultados, gráficos e interpretaciones |
| `tp3_analisis/graficos/` | Gráficos generados |
| `tp3_analisis/registro_uso_ia_tp3.md` | Registro del uso de IA del TP 3 |

## Cómo ejecutar

    python -m pip install pandas openpyxl matplotlib
    python tp2_limpieza/limpieza_datos.py
    python tp3_analisis/analisis_tp3.py