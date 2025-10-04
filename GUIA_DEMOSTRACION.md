# Guía de Uso del Sistema

## 🎯 Objetivo
Utilizar todas las funcionalidades del Sistema Distribuido de Préstamo de Libros de manera efectiva.

## 🚀 Inicio Rápido

### Opción 1: Script Automático (Recomendado)
```bash
./demo.sh
```

### Opción 2: Python Directo
```bash
python demo_profesor.py
```

---

## 📋 Secuencia de Uso (15 minutos)

### **Paso 1: Configuración Inicial (2 minutos)**
1. Ejecutar: `./demo.sh`
2. Seleccionar opción **1**: "Configurar Datos Iniciales"
3. **Verificar:**
   - ✅ 1000 libros generados
   - ✅ 200 libros ya prestados (50 en sitio A, 150 en sitio B)
   - ✅ Copias idénticas en ambas sedes
   - ✅ Campos requeridos: código, título, disponible

### **Paso 2: Iniciar Sistema (2 minutos)**
1. Seleccionar opción **2**: "Iniciar Sistema Distribuido"
2. **Verificar:**
   - ✅ Sitio A: GC + Actores (Renovación, Devolución)
   - ✅ Sitio B: GA + Replicación
   - ✅ Comunicación ZeroMQ entre sitios
   - ✅ Estado de todos los componentes

### **Paso 3: Demostrar RENOVAR (3 minutos)**
1. Seleccionar opción **3**: "Demostrar RENOVAR"
2. **Explicar el flujo:**
   - PS → GC (REQ/REP)
   - GC responde inmediatamente "RECIBIDO"
   - GC → AR (PUB/SUB en tópico RENOVACION)
   - AR → GA (REQ/REP)
   - GA actualiza base de datos
3. **Verificar en pantalla:**
   - Solicitud enviada
   - Respuesta inmediata
   - Logs de procesamiento

### **Paso 4: Demostrar DEVOLVER (3 minutos)**
1. Seleccionar opción **4**: "Demostrar DEVOLVER"
2. **Explicar el flujo:**
   - PS → GC (REQ/REP)
   - GC responde inmediatamente "RECIBIDO"
   - GC → AD (PUB/SUB en tópico DEVOLUCION)
   - AD → GA (REQ/REP)
   - GA actualiza base de datos
3. **Verificar en pantalla:**
   - Solicitud enviada
   - Respuesta inmediata
   - Logs de procesamiento

### **Paso 5: Generación de Carga (3 minutos)**
1. Seleccionar opción **5**: "Mostrar Archivo Peticiones"
   - Mostrar formato: `OPERACION CODIGO_LIBRO USUARIO`
   - Mostrar que tiene 20+ requerimientos
2. Seleccionar opción **6**: "Ejecutar Generación de Carga"
   - Múltiples PS simultáneos
   - Lectura automática desde archivo
   - Comunicación distribuida

### **Paso 6: Visualización de Logs (2 minutos)**
1. Seleccionar opción **7**: "Ver Logs en Tiempo Real"
2. **Verificar:**
   - Comunicación entre componentes
   - Flujo completo PS → GC → Actor → GA
   - Actualizaciones de base de datos

---

## 🎯 Puntos Clave para Enfatizar

### **✅ Comunicación ZeroMQ**
- **REQ/REP**: PS ↔ GC, Actores ↔ GA
- **PUB/SUB**: GC → Actores (Renovación, Devolución)
- **Comunicación distribuida** entre máquinas

### **✅ Operaciones Implementadas**
- **RENOVAR**: Respuesta inmediata + procesamiento asíncrono
- **DEVOLVER**: Respuesta inmediata + procesamiento asíncrono
- **Máximo 2 renovaciones** por libro
- **Una semana adicional** por renovación

### **✅ Generación de Carga**
- **Lectura automática** desde archivo peticiones.txt
- **Múltiples PS** simultáneos
- **20+ requerimientos** de los tres tipos
- **Distribución en máquinas**

### **✅ Datos Iniciales**
- **1000 libros** en total
- **200 libros prestados** (50 sitio A, 150 sitio B)
- **Campos mínimos**: código, título, disponible
- **Copias idénticas** en ambas sedes

### **✅ Logs y Visualización**
- **Flujo completo visible**: PS → GC → Actor → GA
- **Respuestas inmediatas** al PS
- **Actualizaciones de BD** en GA
- **Comunicación distribuida** clara

---

## 🚨 Solución de Problemas

### **Si el sistema no inicia:**
1. Verificar Docker: `docker --version`
2. Verificar puertos: `netstat -an | grep 5555`
3. Reinstalar dependencias: `pip install -r requirements.txt`

### **Si las operaciones fallan:**
1. Verificar que el sistema esté iniciado (opción 2)
2. Verificar logs en tiempo real (opción 7)
3. Reiniciar sistema si es necesario

### **Si no hay datos:**
1. Ejecutar opción 1: "Configurar Datos Iniciales"
2. Verificar archivos en `data/siteA/` y `data/siteB/`

---

## 📊 Resultados Esperados

### **Al final de la demostración, el profesor debe ver:**
- ✅ Sistema funcionando en 2 máquinas (simuladas con Docker)
- ✅ Operaciones RENOVAR y DEVOLVER funcionando
- ✅ Comunicación ZeroMQ (REQ/REP y PUB/SUB)
- ✅ Generación de carga automática
- ✅ Logs claros del flujo completo
- ✅ Actualizaciones en base de datos
- ✅ 1000 libros con 200 préstamos iniciales

---

## 🎯 Comandos de Respaldo

Si algo falla, puede usar estos comandos manuales:

```bash
# Generar datos
python tools/seed_data.py --data-dir ./data/siteA --site A
python tools/seed_data.py --data-dir ./data/siteB --site B

# Iniciar sistema
docker-compose up -d

# Probar operación
python -c "
import zmq, json, time
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://localhost:5555')
socket.send_json({'id': 'test', 'sedeId': 'A', 'userId': 'u-1', 'op': 'RENOVAR', 'libroCodigo': 'ISBN-0001', 'timestamp': int(time.time() * 1000)})
print(socket.recv_json())
socket.close()
context.term()
"

# Ver logs
docker-compose logs -f

# Detener sistema
docker-compose down
```

---

**¡La demostración está lista! Solo siga los pasos numerados en orden.**
