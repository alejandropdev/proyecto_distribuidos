# Informe de Rendimiento - Sistema Distribuido de Préstamo de Libros

## 1. Introducción

Este informe presenta los resultados de los experimentos de rendimiento realizados sobre el Sistema Distribuido de Préstamo de Libros, comparando el rendimiento entre dos modos de operación del Gestor de Carga (GC):

- **Modo Serial**: Procesamiento secuencial de solicitudes en un solo thread
- **Modo Multithread**: Procesamiento concurrente usando múltiples workers

### Objetivos

1. Comparar el tiempo promedio de respuesta entre modo serial y multithread
2. Analizar el throughput (solicitudes procesadas por unidad de tiempo)
3. Evaluar la desviación estándar de los tiempos de respuesta
4. Determinar el impacto del número de procesos solicitantes (PS) en el rendimiento

## 2. Metodología Experimental

### 2.1 Configuración de Experimentos

Se ejecutaron 6 experimentos con las siguientes configuraciones:

| Experimento | Modo | PS SEDE_1 | PS SEDE_2 | Workers | Duración |
|-------------|------|-----------|-----------|---------|----------|
| 1 | Serial | 2 | 2 | 1 | 2 min |
| 2 | Serial | 3 | 3 | 1 | 2 min |
| 3 | Serial | 5 | 5 | 1 | 2 min |
| 4 | Multithread | 2 | 2 | 4 | 2 min |
| 5 | Multithread | 3 | 3 | 4 | 2 min |
| 6 | Multithread | 5 | 5 | 4 | 2 min |

### 2.2 Variables de Medición

- **Tiempo de respuesta**: Tiempo transcurrido desde el envío de la solicitud hasta la recepción de la respuesta (en milisegundos)
- **Throughput**: Número de préstamos procesados en una ventana de 2 minutos
- **Desviación estándar**: Variabilidad de los tiempos de respuesta

### 2.3 Procedimiento

1. Levantar servicios principales (GA, GC, Actor Préstamo)
2. Generar archivo de solicitudes con suficientes préstamos para 2 minutos
3. Ejecutar múltiples instancias de PS en paralelo
4. Registrar métricas durante 2 minutos
5. Analizar resultados

## 3. Especificaciones de Hardware y Software

### 3.1 Hardware

- **Procesador**: [Completar con especificaciones del sistema de prueba]
- **Memoria RAM**: [Completar]
- **Sistema Operativo**: [Completar]

### 3.2 Software

- **Python**: 3.x
- **ZeroMQ**: [Versión]
- **Docker**: [Versión]
- **Docker Compose**: [Versión]

### 3.3 Configuración del Sistema

- **Red Docker**: Bridge network
- **Contenedores**: 3 servicios principales (GA, GC, Actor Préstamo)
- **Workers (modo multithread)**: 4 workers por defecto

## 4. Resultados

### 4.1 Tabla de Resultados

| Modo | PS SEDE_1 | PS SEDE_2 | Total PS | Workers | Total Préstamos | Tiempo Promedio (ms) | Desv. Est. (ms) | Préstamos 2min |
|------|-----------|-----------|----------|---------|-----------------|---------------------|-----------------|----------------|
| Serial | 2 | 2 | 4 | 1 | [Completar] | [Completar] | [Completar] | [Completar] |
| Serial | 3 | 3 | 6 | 1 | [Completar] | [Completar] | [Completar] | [Completar] |
| Serial | 5 | 5 | 10 | 1 | [Completar] | [Completar] | [Completar] | [Completar] |
| Multithread | 2 | 2 | 4 | 4 | [Completar] | [Completar] | [Completar] | [Completar] |
| Multithread | 3 | 3 | 6 | 4 | [Completar] | [Completar] | [Completar] | [Completar] |
| Multithread | 5 | 5 | 10 | 4 | [Completar] | [Completar] | [Completar] | [Completar] |

### 4.2 Gráficos

#### Gráfico 1: Tiempo Promedio de Respuesta vs Número de PS

```
[Insertar gráfico de líneas comparando modo serial vs multithread]
Eje X: Número total de PS (4, 6, 10)
Eje Y: Tiempo promedio de respuesta (ms)
```

#### Gráfico 2: Throughput vs Número de PS

```
[Insertar gráfico de barras comparando modo serial vs multithread]
Eje X: Número total de PS (4, 6, 10)
Eje Y: Préstamos procesados en 2 minutos
```

#### Gráfico 3: Desviación Estándar vs Número de PS

```
[Insertar gráfico comparando variabilidad]
Eje X: Número total de PS (4, 6, 10)
Eje Y: Desviación estándar (ms)
```

### 4.3 Análisis Comparativo

#### Comparación Serial vs Multithread (4 PS)

| Métrica | Serial | Multithread | Mejora |
|---------|--------|-------------|--------|
| Tiempo Promedio (ms) | [Completar] | [Completar] | [Completar]% |
| Throughput (préstamos/2min) | [Completar] | [Completar] | [Completar]% |
| Desviación Estándar (ms) | [Completar] | [Completar] | - |

#### Comparación Serial vs Multithread (6 PS)

| Métrica | Serial | Multithread | Mejora |
|---------|--------|-------------|--------|
| Tiempo Promedio (ms) | [Completar] | [Completar] | [Completar]% |
| Throughput (préstamos/2min) | [Completar] | [Completar] | [Completar]% |
| Desviación Estándar (ms) | [Completar] | [Completar] | - |

#### Comparación Serial vs Multithread (10 PS)

| Métrica | Serial | Multithread | Mejora |
|---------|--------|-------------|--------|
| Tiempo Promedio (ms) | [Completar] | [Completar] | [Completar]% |
| Throughput (préstamos/2min) | [Completar] | [Completar] | [Completar]% |
| Desviación Estándar (ms) | [Completar] | [Completar] | - |

## 5. Discusión

### 5.1 Análisis de Resultados

[Completar con análisis detallado de los resultados]

**Puntos clave a discutir:**
- Impacto del modo multithread en el tiempo de respuesta
- Escalabilidad del sistema con más procesos solicitantes
- Variabilidad de los tiempos de respuesta
- Cuellos de botella identificados

### 5.2 Factores que Afectan el Rendimiento

1. **Número de Workers**: En modo multithread, más workers permiten procesar más solicitudes concurrentemente
2. **Número de PS**: Más procesos solicitantes generan más carga en el sistema
3. **Operaciones de Base de Datos**: Las operaciones de lectura/escritura en GA pueden ser un cuello de botella
4. **Red Docker**: La comunicación entre contenedores introduce latencia

### 5.3 Limitaciones

- Los experimentos se ejecutaron en un entorno controlado (Docker en una sola máquina)
- No se consideraron fallos de red o servicios
- El sistema de base de datos (JSON) no es óptimo para alta concurrencia

## 6. Conclusiones

### 6.1 Hallazgos Principales

1. [Completar con conclusiones principales]
2. [Completar]
3. [Completar]

### 6.2 Recomendaciones

1. **Para cargas bajas**: Modo serial es suficiente y más simple
2. **Para cargas altas**: Modo multithread ofrece mejor rendimiento
3. **Optimizaciones futuras**: 
   - Considerar base de datos más eficiente (PostgreSQL, MongoDB)
   - Implementar caché para operaciones de lectura frecuentes
   - Aumentar número de workers según carga esperada

### 6.3 Trabajo Futuro

- Experimentos con más procesos solicitantes (20, 50, 100)
- Análisis de rendimiento con diferentes números de workers
- Pruebas de stress testing
- Análisis de uso de recursos (CPU, memoria)

## 7. Referencias

- Documentación de ZeroMQ: [URL]
- Documentación de Docker: [URL]
- Enunciado del proyecto: `Enunciado.pdf`

## Anexos

### Anexo A: Scripts de Experimentos

Ver `experimentos_rendimiento.py` para el código completo de los experimentos.

### Anexo B: Datos Crudos

Los datos completos de los experimentos están disponibles en:
- `logs/resultados_experimentos.json`
- `logs/metricas.csv`
- `logs/reporte_rendimiento.md`

### Anexo C: Configuración del Sistema

Ver `docker-compose.yml` y `README.md` para detalles de configuración.

