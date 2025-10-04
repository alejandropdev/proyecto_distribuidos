# Arquitectura del Sistema Distribuido de Préstamo de Libros

## 🏗️ Visión General

El sistema implementa una arquitectura distribuida basada en microservicios, donde cada componente ejecuta en un contenedor Docker independiente, simulando computadoras separadas en una red privada.

## 🐳 Despliegue de Contenedores

### Red Docker
- **Nombre**: `red_distribuida`
- **Tipo**: Bridge
- **Driver**: `bridge`
- **Propósito**: Comunicación entre contenedores

### Contenedores del Sistema

#### 1. Gestor de Carga (GC)
- **Contenedor**: `gc`
- **Imagen**: `sistema_distribuido-gc:latest`
- **Puertos expuestos**:
  - `5001:5001` (REQ/REP)
  - `5002:5002` (PUB/SUB)
- **Red**: `red_distribuida`
- **Volúmenes**:
  - `./data:/app/data` (base de datos)
  - `./logs:/app/logs` (logs del sistema)

#### 2. Actor de Devolución
- **Contenedor**: `actor_dev`
- **Imagen**: `sistema_distribuido-actor_devolucion:latest`
- **Puertos**: Ninguno (solo suscripción)
- **Red**: `red_distribuida`
- **Volúmenes**:
  - `./data:/app/data` (base de datos)
  - `./logs:/app/logs` (logs del sistema)

#### 3. Actor de Renovación
- **Contenedor**: `actor_ren`
- **Imagen**: `sistema_distribuido-actor_renovacion:latest`
- **Puertos**: Ninguno (solo suscripción)
- **Red**: `red_distribuida`
- **Volúmenes**:
  - `./data:/app/data` (base de datos)
  - `./logs:/app/logs` (logs del sistema)

#### 4. Proceso Solicitante (PS)
- **Contenedor**: `ps`
- **Imagen**: `sistema_distribuido-ps:latest`
- **Puertos**: Ninguno (solo cliente)
- **Red**: `red_distribuida`
- **Perfil**: `demo` (no se ejecuta en pruebas)
- **Volúmenes**:
  - `./data:/app/data` (archivo de solicitudes)
  - `./logs:/app/logs` (logs del sistema)

#### 5. Tester (Solo para pruebas)
- **Contenedor**: `tester`
- **Imagen**: `sistema_distribuido-tester:latest`
- **Puertos**: Ninguno
- **Red**: `red_distribuida`
- **Volúmenes**:
  - `./:/app` (código fuente completo)
  - `./data:/app/data` (acceso a datos)
  - `./logs:/app/logs` (escritura de logs)

## 🌐 Distribución de IPs

### Criterio "≥2 Computadores"
El sistema cumple el requisito de distribución mediante:

1. **IPs únicas por contenedor**: Cada contenedor obtiene una IP única en la red Docker
2. **Resolución DNS**: Los contenedores se comunican por nombre (`gc:5001`)
3. **Aislamiento de red**: Cada contenedor tiene su propio namespace de red

### Ejemplo de IPs
```
gc IP: 172.20.0.2
actor_dev IP: 172.20.0.3  
actor_ren IP: 172.20.0.4
ps IP: 172.20.0.5
tester IP: 172.20.0.6
```

**Verificación**: `./scripts/show_ips.sh` confirma ≥2 IPs distintas

## 🔌 Patrones de Comunicación

### REQ/REP (Request-Reply)
- **Componentes**: PS ↔ GC
- **Protocolo**: TCP
- **Endpoint**: `tcp://gc:5001`
- **Características**:
  - Síncrono
  - ACK inmediato (< 500ms)
  - Un solo cliente por vez
  - Confiable (garantiza entrega)

### PUB/SUB (Publish-Subscribe)
- **Componentes**: GC → Actores
- **Protocolo**: TCP
- **Endpoint**: `tcp://gc:5002`
- **Topics**:
  - `devolucion` → Actor de Devolución
  - `renovacion` → Actor de Renovación
- **Características**:
  - Asíncrono
  - Múltiples suscriptores
  - Fire-and-forget
  - No garantiza entrega

## 📁 Estructura de Archivos

### Directorio Raíz
```
sistema_distribuido/
├── gestor_carga.py          # Servicio GC
├── proceso_solicitante.py   # Servicio PS  
├── actor_devolucion.py      # Actor de Devolución
├── actor_renovacion.py      # Actor de Renovación
├── data/                    # Datos compartidos
│   ├── libros.json          # Base de datos
│   └── solicitudes.txt      # Archivo de carga
├── tests/                   # Suite de pruebas
│   ├── test_end_to_end.py
│   ├── test_pubsub_visibility.py
│   ├── test_file_workload.py
│   └── test_utils.py
├── scripts/                 # Scripts de orquestación
│   ├── run_tests.sh
│   ├── collect_evidence.sh
│   ├── show_ips.sh
│   └── wait_for_gc.sh
├── docs/                    # Documentación
│   ├── arquitectura.md
│   ├── pruebas.md
│   ├── evidencias.md
│   ├── metricas.md
│   └── interaccion.md
├── logs/                    # Logs del sistema
├── requirements.txt         # Dependencias Python
├── Dockerfile              # Imagen base
├── docker-compose.yml      # Orquestación
├── Makefile               # Comandos de conveniencia
└── README.md              # Documentación principal
```

### Volúmenes Compartidos
- **`./data`**: Base de datos JSON y archivo de solicitudes
- **`./logs`**: Logs de todos los servicios
- **`./`** (tester): Código fuente completo para pruebas

## 🔧 Configuración de Red

### Docker Compose Network
```yaml
networks:
  red_distribuida:
    driver: bridge
    name: red_distribuida
```

### Resolución DNS
Los contenedores se comunican usando nombres de servicio:
- `gc:5001` → Gestor de Carga REQ/REP
- `gc:5002` → Gestor de Carga PUB/SUB

### Aislamiento
- **Red interna**: Solo contenedores del sistema
- **Puertos expuestos**: Solo GC (5001, 5002)
- **Acceso externo**: Solo a través de puertos mapeados

## 📊 Flujo de Datos

### 1. Inicialización
```
Docker Compose → Levanta contenedores → Configura red → Inicia servicios
```

### 2. Procesamiento de Solicitud
```
PS → Lee archivo → Envía REQ → GC → Responde ACK → Publica evento → Actor → Actualiza BD
```

### 3. Persistencia
```
Actor → Lee libros.json → Modifica datos → Escribe libros.json → Logs evento
```

## 🛡️ Consideraciones de Seguridad

### Aislamiento de Contenedores
- **Namespaces**: Cada contenedor tiene su propio namespace
- **Cgroups**: Limitación de recursos por contenedor
- **Red**: Comunicación solo dentro de la red Docker

### Acceso a Archivos
- **Bind mounts**: Solo directorios necesarios
- **Permisos**: Lectura/escritura según necesidad
- **Aislamiento**: Cada contenedor ve solo sus volúmenes

### Comunicación de Red
- **Protocolo**: TCP (confiable)
- **Autenticación**: Ninguna (red interna)
- **Cifrado**: Ninguno (red privada)

## 📈 Escalabilidad

### Escalado Horizontal
- **Actores**: Múltiples instancias pueden suscribirse al mismo topic
- **PS**: Múltiples instancias pueden enviar solicitudes
- **GC**: Una sola instancia (punto único de falla)

### Escalado Vertical
- **Recursos**: Aumentar CPU/memoria por contenedor
- **Throughput**: Reducir sleep en PS
- **Latencia**: Optimizar procesamiento en actores

### Limitaciones
- **Base de datos**: Archivo JSON (no escalable)
- **GC**: Cuello de botella (una sola instancia)
- **Red**: Ancho de banda de Docker

## 🔍 Monitoreo y Observabilidad

### Logs Centralizados
- **Ubicación**: `./logs/`
- **Formato**: Timestamp + Servicio + Nivel + Mensaje
- **Rotación**: Manual (no implementada)

### Métricas Básicas
- **Latencia**: Tiempo de respuesta REQ/REP
- **Throughput**: Operaciones por segundo
- **Errores**: Conteo de fallos por servicio

### Health Checks
- **Docker**: Health checks cada 30 segundos
- **Aplicación**: Verificación de conectividad ZeroMQ
- **Datos**: Verificación de acceso a archivos

## 🚀 Despliegue

### Desarrollo Local
```bash
# Construir y levantar
docker compose up --build

# Solo servicios básicos
make up

# Con PS (demo)
make demo
```

### Pruebas
```bash
# Suite completa
make test

# Recolectar evidencias
make evidence

# Ver logs
make logs
```

### Producción
```bash
# Levantar en background
docker compose up -d

# Verificar estado
docker compose ps

# Monitorear logs
docker compose logs -f
```

## 🔧 Troubleshooting

### Problemas de Red
```bash
# Verificar conectividad
docker compose run --rm tester ping gc

# Inspeccionar red
docker network inspect red_distribuida

# Ver IPs
./scripts/show_ips.sh
```

### Problemas de Servicios
```bash
# Estado de contenedores
docker compose ps

# Logs de servicio específico
docker logs gc
docker logs actor_dev
docker logs actor_ren
docker logs ps

# Reiniciar servicio
docker compose restart gc
```

### Problemas de Datos
```bash
# Verificar archivos
ls -la data/
cat data/libros.json
cat data/solicitudes.txt

# Verificar permisos
docker compose run --rm tester ls -la /app/data/
```

## 📋 Checklist de Arquitectura

### Requisitos Cumplidos
- [ ] **≥3 procesos**: GC + 2 Actores + PS = 4 procesos
- [ ] **≥2 computadores**: IPs distintas en red Docker
- [ ] **Comunicación TCP**: REQ/REP y PUB/SUB sobre TCP
- [ ] **Patrones ZeroMQ**: Implementados correctamente
- [ ] **Distribución real**: Contenedores independientes
- [ ] **Aislamiento**: Cada proceso en su propio contenedor

### Características Técnicas
- [ ] **Red Docker**: Configurada y funcional
- [ ] **Resolución DNS**: Nombres de servicio funcionando
- [ ] **Volúmenes compartidos**: Datos accesibles por todos
- [ ] **Logs centralizados**: Directorio compartido
- [ ] **Health checks**: Monitoreo básico implementado

### Observabilidad
- [ ] **Logs estructurados**: Timestamp + servicio + mensaje
- [ ] **Métricas básicas**: Latencia, throughput, errores
- [ ] **Evidencias**: Recolección automática de datos
- [ ] **Trazabilidad**: Flujo completo documentado
