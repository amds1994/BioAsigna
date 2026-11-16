# Resumen de experimentos (ejecución real)

Cada fila resume las corridas de un algoritmo en un escenario. J: menor es mejor. `factibles` = corridas con reparto válido. Los algoritmos estocásticos usan las mismas semillas.

## Calidad por algoritmo

| Escenario | Algoritmo | Factibles | J mediana | J Q1–Q3 | J mín–máx | max u (med.) | σ (med.) | Tiempo ms (med.) |
|---|---|---|---|---|---|---|---|---|
| base_6x3 | Óptimo exacto | 1/1 | 0.3000 | 0.3000–0.3000 | 0.3000–0.3000 | 0.5000 | 0.0000 | 0.2 |
| base_6x3 | Voraz | 1/1 | 0.3000 | 0.3000–0.3000 | 0.3000–0.3000 | 0.5000 | 0.0000 | 0.1 |
| base_6x3 | Algoritmo genético | 30/30 | 0.3000 | 0.3000–0.3000 | 0.3000–0.3000 | 0.5000 | 0.0000 | 29.1 |
| base_6x3 | Búsqueda local | 30/30 | 0.3927 | 0.3000–0.3927 | 0.3000–0.3927 | 0.6000 | 0.0817 | 12.3 |
| base_6x3 | Aleatorio factible | 30/30 | 0.5064 | 0.4853–0.5780 | 0.3000–0.7633 | 0.7000 | 0.2160 | 0.0 |
| carga_moderada_20x5 | Voraz | 1/1 | 0.3334 | 0.3334–0.3334 | 0.3334–0.3334 | 0.5500 | 0.0086 | 0.1 |
| carga_moderada_20x5 | Algoritmo genético | 30/30 | 0.3294 | 0.3281–0.3300 | 0.3238–0.3349 | 0.5444 | 0.0069 | 44.9 |
| carga_moderada_20x5 | Búsqueda local | 30/30 | 0.3399 | 0.3337–0.3520 | 0.3307–0.3731 | 0.5571 | 0.0146 | 18.3 |
| carga_moderada_20x5 | Aleatorio factible | 30/30 | 0.5926 | 0.5375–0.6534 | 0.4222–0.7327 | 0.8583 | 0.2050 | 0.1 |
| heterogeneidad_30x6 | Voraz | 1/1 | 0.4712 | 0.4712–0.4712 | 0.4712–0.4712 | 0.7500 | 0.0529 | 0.1 |
| heterogeneidad_30x6 | Algoritmo genético | 30/30 | 0.4603 | 0.4603–0.4604 | 0.4601–0.4621 | 0.7500 | 0.0259 | 55.2 |
| heterogeneidad_30x6 | Búsqueda local | 30/30 | 0.4612 | 0.4608–0.4621 | 0.4603–0.4647 | 0.7500 | 0.0280 | 21.8 |
| heterogeneidad_30x6 | Aleatorio factible | 30/30 | 0.6297 | 0.6000–0.6714 | 0.5676–0.6909 | 0.9167 | 0.1790 | 0.1 |
| escala_150x12 | Voraz | 1/1 | 0.5187 | 0.5187–0.5187 | 0.5187–0.5187 | 0.8583 | 0.0092 | 0.4 |
| escala_150x12 | Algoritmo genético | 30/30 | 0.5310 | 0.5249–0.5393 | 0.5187–0.5484 | 0.8750 | 0.0161 | 272.4 |
| escala_150x12 | Búsqueda local | 30/30 | 0.5178 | 0.5175–0.5187 | 0.5117–0.5209 | 0.8583 | 0.0066 | 88.7 |
| escala_150x12 | Aleatorio factible | 30/30 | 0.6652 | 0.6589–0.6720 | 0.6504–0.6794 | 1.0000 | 0.1631 | 0.4 |
| cambio_entorno_antes | Voraz | 1/1 | 0.3334 | 0.3334–0.3334 | 0.3334–0.3334 | 0.5500 | 0.0086 | 0.1 |
| cambio_entorno_antes | Algoritmo genético | 30/30 | 0.3294 | 0.3281–0.3300 | 0.3238–0.3349 | 0.5444 | 0.0069 | 44.5 |
| cambio_entorno_antes | Búsqueda local | 30/30 | 0.3399 | 0.3337–0.3520 | 0.3307–0.3731 | 0.5571 | 0.0146 | 18.2 |
| cambio_entorno_antes | Aleatorio factible | 30/30 | 0.5926 | 0.5375–0.6534 | 0.4222–0.7327 | 0.8583 | 0.2050 | 0.1 |
| cambio_entorno_despues | Voraz | 1/1 | 0.5062 | 0.5062–0.5062 | 0.5062–0.5062 | 0.8143 | 0.0441 | 0.1 |
| cambio_entorno_despues | Algoritmo genético | 30/30 | 0.4670 | 0.4670–0.4689 | 0.4670–0.4735 | 0.7750 | 0.0049 | 50.0 |
| cambio_entorno_despues | Búsqueda local | 30/30 | 0.4808 | 0.4743–0.4890 | 0.4670–0.5130 | 0.7906 | 0.0178 | 18.5 |
| cambio_entorno_despues | Aleatorio factible | 30/30 | 0.6628 | 0.6239–0.6779 | 0.5494–0.7044 | 0.9698 | 0.1961 | 0.1 |
| sobrecarga_previa | Óptimo exacto | 1/1 | 0.8650 | 0.8650–0.8650 | 0.8650–0.8650 | 1.2000 | 0.3624 | 14.8 |
| sobrecarga_previa | Voraz | 1/1 | 0.8650 | 0.8650–0.8650 | 0.8650–0.8650 | 1.2000 | 0.3624 | 0.0 |
| sobrecarga_previa | Algoritmo genético | 30/30 | 0.8650 | 0.8650–0.8650 | 0.8650–0.8650 | 1.2000 | 0.3624 | 39.4 |
| sobrecarga_previa | Búsqueda local | 30/30 | 0.8650 | 0.8650–0.8650 | 0.8650–0.8651 | 1.2000 | 0.3624 | 16.1 |
| sobrecarga_previa | Aleatorio factible | 30/30 | 0.8667 | 0.8654–0.8709 | 0.8650–0.8766 | 1.2000 | 0.3667 | 0.0 |
| saturacion | Voraz | 0/1 | — (infactible_demostrada) | — | — | — | — | 0.0 |
| saturacion | Algoritmo genético | 0/30 | — (infactible_demostrada) | — | — | — | — | 0.0 |
| saturacion | Búsqueda local | 0/30 | — (infactible_demostrada) | — | — | — | — | 0.0 |
| saturacion | Aleatorio factible | 0/30 | — (infactible_demostrada) | — | — | — | — | 0.0 |
| sin_competente | Voraz | 0/1 | — (infactible_demostrada) | — | — | — | — | 0.0 |
| sin_competente | Algoritmo genético | 0/30 | — (infactible_demostrada) | — | — | — | — | 0.0 |
| sin_competente | Búsqueda local | 0/30 | — (infactible_demostrada) | — | — | — | — | 0.0 |
| sin_competente | Aleatorio factible | 0/30 | — (infactible_demostrada) | — | — | — | — | 0.0 |
| empaquetado_dificil | Voraz | 0/1 | — (sin_solucion_encontrada) | — | — | — | — | 0.0 |
| empaquetado_dificil | Algoritmo genético | 0/30 | — (sin_solucion_encontrada) | — | — | — | — | 43.1 |
| empaquetado_dificil | Búsqueda local | 0/30 | — (sin_solucion_encontrada) | — | — | — | — | 12.8 |
| empaquetado_dificil | Aleatorio factible | 0/30 | — (sin_solucion_encontrada) | — | — | — | — | 1.0 |

## AG frente a cada referencia (mismas semillas)

`AG mejor` = corridas donde el AG obtuvo menor J. La diferencia es J(AG) − J(referencia): negativa favorece al AG. `p` es de una prueba de signos exacta bilateral (empates excluidos).

| Escenario | Referencia | Pares | AG mejor | Empate | AG peor | Mediana ΔJ | p |
|---|---|---|---|---|---|---|---|
| base_6x3 | Voraz | 30 | 0 | 30 | 0 | +0.0000 | 1.0000 |
| base_6x3 | Búsqueda local | 30 | 18 | 12 | 0 | -0.0927 | <0.0001 |
| base_6x3 | Aleatorio factible | 30 | 29 | 1 | 0 | -0.2064 | <0.0001 |
| carga_moderada_20x5 | Voraz | 30 | 25 | 0 | 5 | -0.0040 | 0.0003 |
| carga_moderada_20x5 | Búsqueda local | 30 | 28 | 1 | 1 | -0.0103 | <0.0001 |
| carga_moderada_20x5 | Aleatorio factible | 30 | 30 | 0 | 0 | -0.2639 | <0.0001 |
| heterogeneidad_30x6 | Voraz | 30 | 30 | 0 | 0 | -0.0108 | <0.0001 |
| heterogeneidad_30x6 | Búsqueda local | 30 | 29 | 0 | 1 | -0.0007 | <0.0001 |
| heterogeneidad_30x6 | Aleatorio factible | 30 | 30 | 0 | 0 | -0.1693 | <0.0001 |
| escala_150x12 | Voraz | 30 | 0 | 0 | 30 | +0.0123 | <0.0001 |
| escala_150x12 | Búsqueda local | 30 | 0 | 0 | 30 | +0.0121 | <0.0001 |
| escala_150x12 | Aleatorio factible | 30 | 30 | 0 | 0 | -0.1341 | <0.0001 |
| cambio_entorno_antes | Voraz | 30 | 25 | 0 | 5 | -0.0040 | 0.0003 |
| cambio_entorno_antes | Búsqueda local | 30 | 28 | 1 | 1 | -0.0103 | <0.0001 |
| cambio_entorno_antes | Aleatorio factible | 30 | 30 | 0 | 0 | -0.2639 | <0.0001 |
| cambio_entorno_despues | Voraz | 30 | 30 | 0 | 0 | -0.0392 | <0.0001 |
| cambio_entorno_despues | Búsqueda local | 30 | 26 | 3 | 1 | -0.0129 | <0.0001 |
| cambio_entorno_despues | Aleatorio factible | 30 | 30 | 0 | 0 | -0.1936 | <0.0001 |
| sobrecarga_previa | Voraz | 30 | 0 | 30 | 0 | +0.0000 | 1.0000 |
| sobrecarga_previa | Búsqueda local | 30 | 5 | 25 | 0 | +0.0000 | 0.0625 |
| sobrecarga_previa | Aleatorio factible | 30 | 28 | 2 | 0 | -0.0017 | <0.0001 |

## Adaptación: solicitudes reasignadas tras el cambio de entorno

Cambio: F2 se ausenta, F4 pierde 30 % de capacidad y llegan 3 solicitudes. De las 20 solicitudes originales, cuántas cambiaron de responsable.

| Algoritmo | Reasignadas |
|---|---|
| AG (30 semillas, mediana [Q1–Q3], mín–máx) | 14 [13–15], 10–18 |
| Voraz (determinista) | 14 |
