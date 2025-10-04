# Pasos de Ejecución del Sistema Distribuido

## 📋 Preparación

### 1. Verificar el entorno
```bash
cd sistema_distribuido
docker --version
docker compose --version
```

**Qué ver:** Versiones de Docker y Docker Compose instaladas.

### 2. Verificar datos iniciales
```bash
echo "=== Estado inicial de libros ==="
cat data/libros.json | python -m json.tool
```

**Qué ver:** Base de datos con 3 libros:
- L001 (1984): 6 ejemplares disponibles
- L002 (El Principito): 4 ejemplares disponibles  
- L003 (Cien Años de Soledad): 8 ejemplares disponibles

### 3. Verificar solicitudes a procesar
```bash
echo "=== Solicitudes a procesar ==="
cat data/solicitudes.txt
```

**Qué ver:** 6 líneas con operaciones:
- 3 RENOVACIONES (L001, L003, L002)
- 3 DEVOLUCIONES (L002, L001, L003)

## 🚀 Ejecución del Sistema

### 4. Levantar servicios principales
```bash
docker compose up --build -d gc actor_devolucion actor_renovacion
```

**Qué ver:** 
- Construcción exitosa de imágenes Docker
- 3 contenedores iniciados: `gc`, `actor_dev`, `actor_ren`
- Estado "Up" para todos los contenedores

### 5. Verificar que los servicios estén funcionando
```bash
docker compose ps
```

**Qué ver:** 
- 3 contenedores en estado "Up"
- Puertos 5001-5002 expuestos para `gc`
- Health checks en progreso o completados

### 6. Ver logs de inicialización
```bash
echo "=== Logs del Gestor de Carga ==="
docker compose logs gc

echo "=== Logs de los Actores ==="
docker compose logs actor_devolucion actor_renovacion
```

**Qué ver:**
- **GC:** "✅ Gestor de Carga iniciado correctamente", "📊 Esperando solicitudes"
- **Actores:** "✅ Conectado al Gestor de Carga", "📡 Suscrito al topic", "✅ Actor iniciado correctamente"

## 📤 Procesamiento de Solicitudes

### 7. Ejecutar el Proceso Solicitante
```bash
docker compose run --rm ps
```

**Qué ver:**
- Lectura de 6 solicitudes desde `data/solicitudes.txt`
- Envío de cada solicitud con confirmación inmediata
- Estadísticas finales: "📤 Total de solicitudes enviadas: 6", "✅ Solicitudes exitosas: 6", "📈 Porcentaje de éxito: 100.0%"

### 8. Ver procesamiento de los Actores
```bash
echo "=== Logs del Actor de Renovación ==="
docker compose logs actor_renovacion

echo "=== Logs del Actor de Devolución ==="
docker compose logs actor_devolucion
```

**Qué ver:**
- **Actor Renovación:** 3 eventos procesados, actualizaciones de fechas de devolución
- **Actor Devolución:** 3 eventos procesados, incrementos en ejemplares disponibles

### 9. Ver logs del Gestor de Carga
```bash
docker compose logs gc
```

**Qué ver:**
- 6 solicitudes recibidas y procesadas
- Eventos enviados a los actores con timestamps
- Respuestas enviadas al Proceso Solicitante

## 📊 Verificación de Resultados

### 10. Verificar cambios en la base de datos
```bash
echo "=== Estado final de libros ==="
cat data/libros.json | python -m json.tool
```

**Qué ver:** Cambios en ejemplares disponibles:
- L001: 6 → 7 ejemplares (+1 por devolución)
- L002: 4 → 5 ejemplares (+1 por devolución)
- L003: 8 → 9 ejemplares (+1 por devolución)

### 11. Mostrar resumen de operaciones
```bash
echo "=== Resumen de operaciones procesadas ==="
echo "Renovaciones: 3 (L001, L003, L002)"
echo "Devoluciones: 3 (L002, L001, L003)"
echo "Total: 6 operaciones exitosas"
echo "Tasa de éxito: 100%"
```

## 🛑 Limpieza

### 12. Detener el sistema
```bash
docker compose down
```

**Qué ver:**
- Contenedores detenidos y removidos
- Red personalizada removida
- Sistema completamente limpio

## ✅ Puntos Clave a Destacar

1. **Comunicación distribuida:** REQ/REP entre PS y GC, PUB/SUB entre GC y Actores
2. **Procesamiento asíncrono:** GC responde inmediatamente, Actores procesan en paralelo
3. **Consistencia de datos:** Base de datos actualizada correctamente por cada Actor
4. **Logs detallados:** Cada componente registra sus operaciones con timestamps
5. **Manejo de errores:** Sistema robusto con confirmaciones y validaciones
6. **Arquitectura escalable:** Fácil agregar más Actores o tipos de operaciones

## 🔍 Verificaciones Adicionales

### Verificar conectividad de red
```bash
docker network ls | grep red_distribuida
```

### Ver logs en tiempo real (opcional)
```bash
docker compose logs -f
```

### Verificar archivos de logs generados
```bash
ls -la logs/
```
