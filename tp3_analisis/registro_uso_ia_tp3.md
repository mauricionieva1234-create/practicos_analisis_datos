# Registro de uso de IA – TP N° 3 (consigna 5)

Consulta analizada: Pregunta 1 (socios vigentes por actividad).
Ciclo: problema → propuesta → análisis → verificación → corrección.

## 1. Problema
Saber cuántos socios vigentes tiene el club y cómo se reparten por actividad.

## 2. Propuesta de la IA
```sql
SELECT actividad,
       COUNT(*) AS socios_vigentes
FROM socios
WHERE categoria <> 'Inactivo'
GROUP BY actividad
ORDER BY socios_vigentes DESC, actividad;
```

## 3. Análisis
Antes de ejecutarla revisé qué significa "socio activo". La columna categoria tiene un
valor llamado "Activo" (14 socios), pero filtrar `categoria = 'Activo'` dejaría afuera a
los Cadete, Vitalicio y Honorario, que también son socios vigentes. Se definió "vigente"
como todos los que no están Inactivos (18 socios). Revisé además que el GROUP BY
agrupe por actividad y que las actividades ya estén unificadas por el TP 2.

## 4. Verificación
- El script calcula lo mismo con pandas y compara contra el resultado de SQL: coinciden.
- [COMPLETAR: verificación manual. Ej.: "Abrí Registro_Socios_LIMPIO.xlsx, filtré la
  columna actividad = Pádel y excluí a Inactivos; conté ___ socios".]
- [COMPLETAR: la suma de la tabla da 18 = 19 socios menos el inactivo (socio 111).]

## 5. Corrección
[COMPLETAR con lo que realmente pasó. Si no hubo que cambiar nada, escribir:
"La consulta fue correcta y no requirió cambios; lo que hubo que decidir fue la
definición de socio vigente".]