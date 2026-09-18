# GBC MARKET X - Guia practica de filtros

## 1. Objetivo

Esta guia explica por que una tactica puede mostrar cifras distintas entre:

- Executive Summary.
- Tactic slide del mes actual.
- Historico de la tactic slide.
- YTD Outcomes.
- YTD Impressions.

Todos los datos son ficticios. El umbral usado en los ejemplos es `$50.00`.

```text
Costo agregado < $50.00  = low spend
Costo agregado >= $50.00 = pasa
```

El valor exacto de `$50.00` pasa.

## 2. Configuracion del ejemplo

| Control | Valor |
|---|---:|
| Brand | GBC |
| Market | MARKET X |
| Report Month | June 2026 |
| Tier | LMA |
| Audience | GEN |
| Minimum Aggregated Spend | $50.00 |
| Historical Window | 6 meses |
| Exclude Months Below Spend Threshold | Activado |
| Min YTD Outcomes | 100 |
| Min YTD Impressions | 1,000 |

## 3. Ejemplo maestro

### 3.1 Filas originales

| Tactica raw | Strategy | Site | Audience | Cost | Impressions | Video Completes | Video Plays | KBAs |
|---|---|---|---|---:|---:|---:|---:|---:|
| FEP | Awareness | ALPHA DSP | GEN | $120.00 | 100,000 | 95,000 | 98,000 | 20 |
| FEP | Awareness | ALPHA TRADE DESK | GEN | $80.00 | 50,000 | 45,000 | 47,000 | 10 |
| FEP | Awareness | BETA | GEN | $25.00 | 20,000 | 19,000 | 20,000 | 5 |
| YouTube | Video | ALPHA | GEN | $50.00 | 60,000 | 2,000 | 2,500 | 8 |
| Display | InMarket | GAMMA | GEN | $30.00 | 40,000 | 0 | 0 | 40 |
| Display | BT | GAMMA | GEN | $19.99 | 50,000 | 0 | 0 | 60 |
| Search | Search | DELTA | GEN | $40.00 | 0 | 0 | 0 | 0 |
| Audio | Audio | ALPHA | GEN | $75.00 | 80,000 | 0 | 0 | 0 |

### 3.2 Combinaciones agregadas

El codigo normaliza y luego agrupa por:

```text
Tactica efectiva + Site agrupado + Audience
```

| Combinacion | Cost agregado | Impressions | KBAs | Estado |
|---|---:|---:|---:|---|
| FEP + ALPHA + GEN | $200.00 | 150,000 | 30 | Pasa |
| FEP + BETA + GEN | $25.00 | 20,000 | 5 | Low spend con performance |
| YouTube + ALPHA + GEN | $50.00 | 60,000 | 8 | Pasa en el limite |
| InMarket Display + GAMMA + GEN | $49.99 | 90,000 | 100 | Low spend con performance |
| Search + DELTA + GEN | $40.00 | 0 | 0 | Low spend sin performance |
| Audio + ALPHA + GEN | $75.00 | 80,000 | 0 | Pasa |

## 4. Orden de aplicacion

```text
1. Filtrar Brand, Market, Month, Tier y Client Code
2. Normalizar Tactica, Strategy y Site
3. Agrupar por Tactica efectiva + Site agrupado + Audience
4. Sumar Cost y metricas
5. Comparar el Cost agregado con $50
6. Aplicar la regla de cada vista
7. Calcular KPI y benchmark
8. Registrar anomalias
```

El filtro de `$50` no se aplica a cada fila original.

### Ejemplo

Las filas FEP ALPHA tienen costos `$120` y `$80`.

```text
$120 + $80 = $200
```

Se evalua `$200`, no cada fila por separado.

## 5. Normalizacion antes del filtro

### Regla 5.1 - Tacticas equivalentes

| Nombre original | Nombre efectivo |
|---|---|
| Pre-roll | PreRoll |
| Preroll | PreRoll |
| OLV | PreRoll |
| Digital Video | PreRoll |
| CTV | FEP |

### Regla 5.2 - Display depende de Strategy

| Strategy | Nombre interno | Nombre visible |
|---|---|---|
| BT, InMarket, Purchase | BT Display | InMarket Display |
| Retargeting | Retargeting Display | Retargeting Display |
| Consideration, HPA | Consideration Display | Consideration Display |
| Vacia o desconocida | BT Display | InMarket Display |

### Ejemplo

```text
Display + InMarket + GAMMA = $30.00
Display + BT + GAMMA       = $19.99
Total InMarket Display     = $49.99
```

Resultado: la combinacion es low spend porque `$49.99 < $50.00`.

### Regla 5.3 - Sites equivalentes se agrupan

Ejemplo:

```text
Ampersand-Spectrum
Ampersand MSP FEP
Ampersand-GEN
```

Los tres pueden convertirse en `AMPERSAND`. Si tactica y audience tambien coinciden, sus costos se suman antes del filtro.

### Regla 5.4 - Social y Meta

| Entrada | Resultado |
|---|---|
| Social Display, Meta Display, Paid Social o site Meta/Facebook/Instagram | Meta Display |
| Social Video o Meta Video | Meta Video |
| Pinterest o TikTok | Conserva su propia tactica |

Ejemplo: una fila `Paid Social` del site `Facebook Ads` se procesa como `Meta Display`; no se mezcla con Pinterest.

## 6. Regla central por vista

| Vista | Combinacion < $50 con performance | Combinacion < $50 sin performance | Combinacion >= $50 |
|---|---|---|---|
| Executive Summary | Excluye | Excluye | Incluye |
| Tactic slide actual | Mantiene y registra anomalia | Omite | Incluye |
| Historico tactic | Remueve el mes si el control esta activo | Remueve el mes | Incluye el mes |
| YTD | No usa spend | No usa spend | No usa spend |

Esta tabla explica la mayoria de las diferencias del deck.

## 7. Tactic slide del mes actual

### Regla 7.1 - Low spend con performance

La slide se mantiene y se registra una anomalia.

#### Ejemplo

FEP BETA:

```text
Cost agregado: $25.00
Impressions: 20,000
Video Completes: 19,000
KBAs: 5
```

Resultado:

- La tactic slide aparece.
- El Error Summary registra low spend con performance.
- Sus metricas no entran al Executive Summary.

### Regla 7.2 - Low spend sin performance

La slide se omite.

#### Ejemplo

Search DELTA:

```text
Cost agregado: $40.00
Impressions: 0
KBAs: 0
Video Completes: 0
Clicks: 0
```

Resultado: no se genera la tactic slide.

### Regla 7.3 - Costo en el limite

YouTube ALPHA tiene `$50.00`.

```text
$50.00 >= $50.00
```

Resultado: pasa y la slide se genera.

## 8. Historico de tactic slides

### Regla 8.1 - Ventana historica

`Historical Window (Months)` define cuantos meses se consideran, terminando en el report month.

Ejemplo con June 2026:

| Valor UI | Periodo |
|---:|---|
| 6 | January a June 2026 |
| 3 | April a June 2026 |
| 1 | June 2026 |

### Regla 8.2 - Filtro mensual de spend

Si `Exclude Months Below Spend Threshold` esta activado, el historico revisa solo el costo mensual agregado.

| Mes FEP ALPHA | Cost | Impressions | Resultado |
|---|---:|---:|---|
| January | $40.00 | 30,000 | Remueve |
| February | $50.00 | 35,000 | Incluye |
| March | $80.00 | 45,000 | Incluye |
| April | $0.00 | 20,000 | Remueve |
| May | $120.00 | 90,000 | Incluye |
| June | $200.00 | 150,000 | Incluye |

January y April se remueven aunque tengan impressions. El historico usa costo, no performance.

Si el control esta desactivado, esos meses no se eliminan por spend.
## 9. Executive Summary

### Regla 9.1 - Filtra combinaciones antes de crear la tarjeta

Para cada audience, el Summary hace lo siguiente:

```text
1. Agrupa por Tactica efectiva + Site agrupado + Audience
2. Excluye cada combinacion con Cost < $50
3. Suma las combinaciones que pasaron por tactica
4. Calcula el KPI de la tarjeta con los totales sobrevivientes
```

La performance no rescata una combinacion low spend en esta vista.

### Ejemplo FEP

| Combinacion | Cost | Impressions | Summary |
|---|---:|---:|---|
| FEP + ALPHA + GEN | $200.00 | 150,000 | Incluye |
| FEP + BETA + GEN | $25.00 | 20,000 | Excluye |

Resultado de la tarjeta FEP:

```text
Impressions = 150,000
```

No muestra `170,000`, porque BETA no pasa el umbral.

### Regla 9.2 - Cuando coincide con la tactic slide

Si ALPHA es la unica combinacion FEP que pasa, entonces:

| Vista | Impressions |
|---|---:|
| Executive Summary - FEP | 150,000 |
| Tactic slide - FEP ALPHA | 150,000 |

La igualdad es correcta. No significa que ambas vistas apliquen exactamente la misma regla; significa que solo una combinacion sobrevivio en el Summary.

### Regla 9.3 - Cuando debe ser diferente

Suponga una segunda combinacion valida:

| Combinacion | Cost | Impressions |
|---|---:|---:|
| FEP + ALPHA + GEN | $200.00 | 150,000 |
| FEP + OMEGA + GEN | $60.00 | 10,000 |

Entonces:

| Vista | Impressions |
|---|---:|
| Executive Summary - FEP | 160,000 |
| Tactic slide - FEP ALPHA | 150,000 |
| Tactic slide - FEP OMEGA | 10,000 |

El Summary consolida sites validos. Cada tactic slide conserva su propio site.

### Regla 9.4 - Una slide por audience

GEN, HIS y otros audiences no se mezclan en la misma slide de Summary. Un audience vacio se trata como GEN.

Ejemplo: `FEP + ALPHA + GEN` y `FEP + ALPHA + HIS` producen tarjetas en summaries distintos.

### Regla 9.5 - Filtro estricto de video para LMA

Despues del filtro de spend, LMA elimina del Summary las tarjetas FEP y YouTube cuyo total de Video Completions sea `0`.

| Tier | Tactica | Cost | Video Completes | Resultado Summary |
|---|---|---:|---:|---|
| LMA | FEP | $200.00 | 0 | Excluye |
| LMA | YouTube | $50.00 | 0 | Excluye |
| LMA | PreRoll | $80.00 | 0 | No aplica esta regla especial |
| ZONE | FEP | $200.00 | 0 | No aplica esta regla especial |

## 10. Regla de video en tactic slides

El control `Skip Video Tactics w/ 0 Completions` revisa tacticas de video normalizadas.

| Video Completes | Impressions o KBAs | Resultado |
|---:|---:|---|
| 0 | 0 | Omite la tactic slide |
| 0 | Mayor que 0 | Mantiene la tactic slide |
| Mayor que 0 | Cualquier valor | Mantiene la tactic slide |

### Ejemplo

FEP OMEGA tiene `$70` de costo, `10,000` impressions y `0` completions. La slide se mantiene porque existe actividad.

Nota de implementacion: el texto de ayuda de la UI dice `LMA only`, pero el bloque que aplica este checkbox en la tactic slide no valida explicitamente el tier. El filtro estricto FEP/YouTube del Executive Summary si valida LMA.

## 11. YTD: filtro por metrica, no por costo

YTD no usa `Minimum Aggregated Spend` ni `Exclude Months Below Spend Threshold`.

### Regla 11.1 - Periodo YTD

Solo incluye el ano seleccionado y meses hasta el report month.

Ejemplo: para June 2026 incluye January-June 2026. No incluye December 2025 ni July 2026.

### Regla 11.2 - YTD Outcomes

Con `Min YTD Outcomes = 100`, se suma el outcome de todas las tacticas por mes.

| Mes | FEP KBAs | Display KBAs | Total | Resultado |
|---|---:|---:|---:|---|
| January | 60 | 39 | 99 | Excluye |
| February | 60 | 40 | 100 | Incluye |

El limite exacto pasa.

### Regla 11.3 - YTD Impressions

Con `Min YTD Impressions = 1,000`, se suman las impressions de todos los vehiculos por mes.

| Mes | Vehicle A | Vehicle B | Total | Resultado |
|---|---:|---:|---:|---|
| March | 600 | 399 | 999 | Excluye |
| April | 700 | 300 | 1,000 | Incluye |

### Regla 11.4 - Checkbox YTD desactivado

Si `Apply YTD Threshold Filter` esta desactivado, no se aplican los minimos `100` y `1,000`. Sin embargo, un mes cuyo total sea `0` se elimina de todos modos.

Ejemplo: un mes con `$0` de costo y `25` KBAs puede aparecer en YTD Outcomes. Un mes con `$500` de costo y `0` KBAs no aparece en ese grafico.

## 12. Alcance real de los controles UI

| Control | Executive Summary | Tactic actual | Historico tactic | YTD | Utilidad real |
|---|---|---|---|---|---|
| Minimum Aggregated Spend (USD) | Si | Si | Si, cuando su checkbox esta activo | No | Define el umbral; `$50` pasa |
| Exclude Months Below Spend Threshold | No | No | Si | No | Activa o desactiva el filtro mensual de costo historico |
| Historical Window (Months) | No | No | Si | No | Define cuantos meses aparecen en charts y KBA tables |
| Skip Video Tactics w/ 0 Completions | No | Si | No | No | Omite video sin completions, impressions ni KBAs |
| Apply YTD Threshold Filter | No | No | No | Si | Activa los minimos mensuales de Outcomes e Impressions |
| Min YTD Outcomes | No | No | No | Si | Minimo del total mensual de outcomes |
| Min YTD Impressions | No | No | No | Si | Minimo del total mensual de impressions |

`Skip $0 Cost & Perf Tactics` fue eliminado. Su funcion ya esta cubierta por la regla central de spend y performance.
## 13. Alcance de mercado

### Regla 13.1 - Market Code tiene prioridad

Si existe un Market Code valido y distinto de `XXXXX`, el codigo identifica el mercado con ese valor. Market Name queda como respaldo.

Ejemplo: `MKTX1` identifica MARKET X aunque el texto del nombre llegue como `MARKET X, PA`.

### Regla 13.2 - Matching estricto y relajado

| Modo | Uso | Ejemplo |
|---|---|---|
| Estricto | Queries de datos y tacticas | `Market Name = MARKET X` |
| Relajado | Descubrimiento inicial | Un nombre que contiene `MARKET X` |

### Regla 13.3 - Filtros acoplados

Cada query incluye Brand, Market, Month Year cuando aplica y Zone/LMA cuando se proporciona.

Ejemplo: datos GBC de MARKET X en June 2026 y LMA no deben mezclarse con otra marca, mercado, mes o tier.

### Regla 13.4 - Client Code depende del tier

| Tier | Client Code |
|---|---|
| LMA | Se conserva como filtro obligatorio |
| ZONE | Se elimina para agregar clientes del Market Code |

## 14. Contenido y orden de tactic slides

### Regla 14.1 - Orden

Orden principal:

```text
FEP -> PreRoll -> YouTube -> InMarket Display -> Consideration Display
-> Retargeting Display -> Meta Display -> Meta Video -> Pinterest
-> TikTok -> Search -> Audio
```

Dentro de FEP: EMRGE, MSP y luego otros. Para la misma tactica, GEN aparece antes de HIS.

### Regla 14.2 - Metricas visibles

| Tactica | Metricas principales |
|---|---|
| FEP | Impressions, Video Completes, VCR |
| PreRoll | Impressions, Video Completes, VCR, Viewability |
| YouTube | Impressions, Video Completes, CPCV, YT Viewability |
| Display variants | Impressions, Total KBAs, CPA, Viewability |
| Meta Display | Impressions, Total KBAs, CPA |
| Meta Video | Impressions, Video Completes, VCR |
| Pinterest Display/Video | Impressions, Total KBAs, CPA |
| TikTok | Impressions, Video Completes, CPCV |
| Search | Impressions, Clicks, CPC |
| Audio | Impressions, Audio Completes, ACR |

### Regla 14.3 - Grafico historico

| Tactica | Barras | Linea |
|---|---|---|
| FEP, PreRoll, Meta Video | Video Completes | VCR |
| YouTube, TikTok | Video Completes | CPCV |
| Display variants, Meta Display, Pinterest | Conversions o KBAs | CPA |
| Search | Clicks | CPC |
| Audio | Audio Completes | ACR |

Ejemplo: la slide FEP usa Video Completes en barras y VCR en la linea, solo para los meses historicos que sobrevivieron al filtro de costo.

## 15. KPI, benchmark y color

### Regla 15.1 - Formulas

| KPI | Formula |
|---|---|
| VCR | Video Completions / Video Plays |
| CPCV | Total Cost / Video Completions |
| CPA | Total Cost / Total Conversions |
| CPC | Total Cost / Clicks |
| ACR | Audio Completes / Audio Starts |
| Viewability | Unique Viewable Impressions / Unique Measured Impressions |
| YT Viewability | Active Viewable Impressions / Active View Measurable Impressions |

Toda division con denominador `0` devuelve `0`.

### Ejemplos

```text
FEP VCR = 140,000 / 145,000 = 96.55%
YouTube CPCV = $50 / 2,000 = $0.025
Display CPA = $200 / 100 = $2.00
Search CPC = $80 / 40 = $2.00
Audio ACR = 7,500 / 8,000 = 93.75%
```

### Regla 15.2 - KPI de la tarjeta Summary

| Tactica | KPI |
|---|---|
| FEP, PreRoll, Meta Video | VCR |
| YouTube, TikTok | CPCV |
| Display variants, Meta Display, Pinterest | CPA |
| Search | CPC |
| Audio | ACR |

El KPI se calcula despues de filtrar y agregar. No se promedian KPIs de filas originales.

### Regla 15.3 - Color contra benchmark

| Tipo de KPI | Verde | Rojo |
|---|---|---|
| CPA, CPCV, CPC | Valor <= benchmark | Valor > benchmark |
| VCR, ACR, CTR | Valor >= benchmark | Valor < benchmark |

Un benchmark `TBD` se muestra neutral negro; `N/A`, neutral gris. Viewability usa `>70%` y YT Viewability usa `>90%` como referencias fijas.

Cuando un benchmark cambia por fecha, se usa la version mas reciente cuya fecha de inicio sea menor o igual al report month.

Ejemplo: con benchmark VCR de `90%`, un FEP de `96.55%` aparece verde.

## 16. Anomalias

| Caso | Accion | Ejemplo |
|---|---|---|
| Low spend con performance | Mantiene tactic slide y registra error | FEP BETA: `$25`, 20,000 impressions |
| VCR mayor a 100% | Registra error y limita el chart a 100% | 105 completions / 100 plays |
| Vehiculo de otra marca en YTD | Registra error y elimina esa serie | Vehicle Z pertenece a otra marca |

El Error Summary aparece solo cuando se detecta al menos una anomalia.

## 17. Estructura y salida del deck

### Orden general

```text
1. Title
2. Executive Summary, uno por audience
3. Tactic slides
4. YTD KBA
5. YTD Impressions by Vehicle
6. Glossary
7. Error Summary, solo si hay anomalias
```

En `summary_only`, no se generan tactic slides ni las secciones opcionales.

### Nombre de archivo

| Tier | Patron |
|---|---|
| LMA | `{prefix} {Brand} {Month Year} Digital Metrics.pptx` |
| ZONE | `{market_code}-{Month Year} {Brand} Zone Reporting.pptx` |

En LMA, `prefix` usa primero el prefijo de UI; si falta, Client Code; si falta, Market Code. Si el nombre ya existe, se agrega el Market Code para evitar colision.

Carpeta esperada:

```text
Generated_Slides/{Zone|LMA}/{Brand}/{MM - MonthName}/{Region}/
```

## 18. Cambio de negocio: antes y ahora

| Elemento | Documento legado | Codigo actual |
|---|---|---|
| Corte de spend | Costo `$0` | Costo menor al umbral UI |
| Valor | `$0` fijo | `$50` inicial y configurable |
| Limite | Un costo mayor que `$0` pasaba | El valor exacto del umbral pasa |
| Tactic actual e historico | Evaluacion en la combinacion de la slide | Conserva esa unidad agregada |
| Executive Summary | Filtraba despues de agregar toda la tactica | Filtra combinaciones y despues consolida la tactica |
| YTD | Filtro por metrica | Sin cambio |

La regla objetivo se cumple en el codigo actual:

```text
Una combinacion con costo agregado menor a $50 se trata como antes
se trataba una combinacion con costo $0.
```

No se filtran filas individuales y spend no se aplica a YTD.

### Precision importante sobre Summary

El cambio de `$0` a `$50` no es la unica diferencia observable frente al documento legado. El punto de aplicacion del filtro en Summary tambien quedo alineado con las tactic slides:

```text
Documento legado: sumar toda FEP -> filtrar la tactica
Codigo actual: filtrar cada FEP + Site + Audience -> sumar los sobrevivientes
```

Esta alineacion evita que un site low spend aporte impressions al Summary. Es la razon por la que el caso FEP puede coincidir con su tactic slide cuando solo un site pasa.

## 19. Diagnostico de diferencias

Si dos slides no coinciden, revise en este orden:

1. Mismo Brand, Market, Month, Tier, Client Code y Audience.
2. Misma tactica efectiva despues de normalizacion.
3. Mismo Site agrupado.
4. Costo agregado de cada combinacion contra el umbral.
5. Si el Summary esta sumando mas de un site valido.
6. Si LMA elimino FEP o YouTube por `0` Video Completions.
7. Si la comparacion es contra un historico filtrado por costo o contra YTD filtrado por metrica.
8. Si existe una anomalia registrada.

### Diagnostico rapido de FEP

```text
Summary FEP = suma de todos los sites FEP validos para el audience
Tactic FEP  = un site agrupado especifico para el audience
```

Si ambos muestran `841,116`, es correcto cuando ese site es el unico FEP que pasa el filtro del Summary. Si existe otro site FEP con costo `>= $50`, el Summary debe ser mayor que esa tactic slide individual.

## 20. Referencias de codigo

| Regla | Archivo |
|---|---|
| Umbral y configuracion | `Scripts/filters_manager.py` |
| Controles UI | `Scripts/app_ui.py` |
| Summary: filtro por combinacion y KPI | `Scripts/measures.py` |
| Summary: filtro estricto LMA | `Scripts/executive_summary.py` |
| Tactic actual, historico, video y YTD | `Scripts/main_slide_generator.py` |
| Normalizacion Display | `Scripts/display_resolution.py` |
| Mapeos, sites y orden | `Scripts/config/normalization_rules.json` |
| Metricas y charts por tactica | `Scripts/tactic_config.py` |

## Resumen ejecutivo

- El costo se suma por `Tactica efectiva + Site agrupado + Audience`.
- Menor a `$50` es low spend; `$50` pasa.
- Executive Summary excluye todas las combinaciones low spend.
- Tactic actual mantiene low spend solo cuando hay performance y registra la anomalia.
- Historico elimina meses low spend cuando su checkbox esta activo.
- YTD filtra por la metrica mensual, no por costo.
- Summary consolida sites validos; la tactic slide muestra un site especifico.
- Normalizacion, KPI, benchmark, orden y anomalias se conservan; Summary ahora filtra combinaciones antes de consolidar la tarjeta.