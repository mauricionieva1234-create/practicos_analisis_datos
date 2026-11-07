-- Consultas SQL del TP N° 3 (se ejecutan sobre SQLite; tabla: socios).
-- El script analisis_tp3.py lee este archivo: cada consulta empieza con "-- name:".
--
-- Definiciones:
--   socio vigente  = categoria <> 'Inactivo' (o categoría desconocida)
--   socio obligado = vigente y estado <> 'EXENTO' (debe pagar cuota)

-- name: q1_socios_por_actividad
SELECT
    actividad,
    COUNT(*) AS socios_vigentes
FROM socios
WHERE (categoria <> 'Inactivo' OR categoria IS NULL)
  AND actividad IS NOT NULL
GROUP BY actividad
ORDER BY socios_vigentes DESC, actividad;


-- name: q2_estado_obligados
SELECT
    estado,
    COUNT(*) AS socios,
    COALESCE(SUM(cuota), 0) AS monto
FROM socios
WHERE (categoria <> 'Inactivo' OR categoria IS NULL)
  AND estado IS NOT NULL
  AND estado <> 'EXENTO'
GROUP BY estado
ORDER BY estado;


-- name: q3_cuota_por_categoria
SELECT
    categoria,
    COUNT(*) AS socios,
    ROUND(AVG(cuota), 0) AS cuota_promedio,
    MIN(cuota) AS cuota_minima,
    MAX(cuota) AS cuota_maxima
FROM socios
WHERE categoria IS NOT NULL
GROUP BY categoria
ORDER BY categoria;


-- name: q4_altas_por_anio
SELECT
    anio_alta,
    COUNT(*) AS altas
FROM socios
WHERE anio_alta IS NOT NULL
GROUP BY anio_alta
ORDER BY anio_alta;