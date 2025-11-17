#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Datos Iniciales - Sistema Distribuido de Préstamo de Libros
Genera la base de datos inicial con 1000 libros según los requerimientos del enunciado
"""

import json
import random
from datetime import datetime, timedelta
import os

def generar_titulos_libros():
    """Genera una lista de títulos de libros realistas"""
    titulos = [
        "El Quijote", "Cien Años de Soledad", "1984", "El Principito", "Don Juan Tenorio",
        "La Divina Comedia", "Hamlet", "Romeo y Julieta", "Macbeth", "El Rey Lear",
        "La Odisea", "La Ilíada", "El Lazarillo de Tormes", "La Celestina", "El Buscón",
        "Las Mil y Una Noches", "Los Miserables", "El Conde de Montecristo", "Los Tres Mosqueteros",
        "Veinte Mil Leguas de Viaje Submarino", "La Vuelta al Mundo en 80 Días", "Viaje al Centro de la Tierra",
        "Frankenstein", "Drácula", "El Retrato de Dorian Gray", "El Extraño Caso del Dr. Jekyll y Mr. Hyde",
        "Alicia en el País de las Maravillas", "A través del Espejo", "El Hobbit", "El Señor de los Anillos",
        "Harry Potter y la Piedra Filosofal", "Harry Potter y la Cámara Secreta", "Harry Potter y el Prisionero de Azkaban",
        "Crónica de una Muerte Anunciada", "El Amor en los Tiempos del Cólera", "Memoria de mis Putas Tristes",
        "La Casa de los Espíritus", "Eva Luna", "Paula", "De Amor y de Sombra", "Hija de la Fortuna",
        "El Aleph", "Ficciones", "El Jardín de Senderos que se Bifurcan", "La Muerte y la Brújula",
        "Rayuela", "Bestiario", "Final del Juego", "Historias de Cronopios y de Famas",
        "Pedro Páramo", "El Llano en Llamas", "La Muerte de Artemio Cruz", "Aura",
        "La Tregua", "Gracias por el Fuego", "El Astillero", "Juntacadáveres",
        "La Guerra y la Paz", "Ana Karenina", "Crimen y Castigo", "Los Hermanos Karamazov",
        "El Idiota", "Memorias del Subsuelo", "El Jugador", "Las Noches Blancas",
        "Orgullo y Prejuicio", "Sentido y Sensibilidad", "Emma", "Mansfield Park",
        "Persuasión", "Northanger Abbey", "Jane Eyre", "Cumbres Borrascosas",
        "El Molino del Floss", "Middlemarch", "Silas Marner", "Adam Bede",
        "Moby Dick", "Bartleby el Escribiente", "Billy Budd", "Typee",
        "Omoo", "Redburn", "White-Jacket", "Israel Potter",
        "El Gran Gatsby", "El Sol También Sale", "Por Quién Doblan las Campanas", "Adiós a las Armas",
        "Tener y No Tener", "Las Nieves del Kilimanjaro", "El Viejo y el Mar", "Islas en el Golfo",
        "Ulises", "Finnegans Wake", "Retrato del Artista Adolescente", "Dublineses",
        "Los Exiliados", "Esteban el Héroe", "Stephen el Héroe", "Giacomo Joyce",
        "En Busca del Tiempo Perdido", "Por el Camino de Swann", "A la Sombra de las Muchachas en Flor",
        "El Mundo de Guermantes", "Sodoma y Gomorra", "La Prisionera", "La Fugitiva",
        "El Tiempo Recobrado", "Los Demonios", "El Doble", "Noches Blancas",
        "El Eterno Marido", "El Adolescente", "Memorias de la Casa Muerta", "Humillados y Ofendidos",
        "El Sueño del Tío", "La Dama de Picas", "La Reina de Espadas", "El Jinete de Bronce",
        "Eugene Onegin", "Boris Godunov", "Ruslán y Liudmila", "El Convite de Piedra",
        "Fausto", "Las Desventuras del Joven Werther", "Los Años de Aprendizaje de Wilhelm Meister",
        "Poesía y Verdad", "Las Afinidades Electivas", "Hermann y Dorotea", "Egmont",
        "Ifigenia en Táuride", "Torquato Tasso", "Clavijo", "Stella",
        "La Metamorfosis", "El Proceso", "El Castillo", "América",
        "La Condena", "En la Colonia Penitenciaria", "Un Artista del Hambre", "La Construcción",
        "El Despertar", "La Casa de la Alegría", "Ethan Frome", "La Edad de la Inocencia",
        "Verano", "Los Hijos", "La Recompensa", "Madame de Treymes",
        "El Sonido y la Furia", "Mientras Agonizo", "Luz de Agosto", "Absalom, Absalom!",
        "Santuario", "Pylon", "El Desierto", "La Mansión",
        "Los Intrusos", "Requiem por una Monja", "Una Fábula", "Los Rateros",
        "El Ruido y la Furia", "Mientras Agonizo", "Luz de Agosto", "Absalom, Absalom!",
        "Santuario", "Pylon", "El Desierto", "La Mansión",
        "Los Intrusos", "Requiem por una Monja", "Una Fábula", "Los Rateros"
    ]
    
    # Agregar más títulos para llegar a 1000
    autores = ["García Márquez", "Borges", "Cortázar", "Paz", "Fuentes", "Vargas Llosa", 
               "Allende", "Neruda", "Mistral", "Donoso", "Skármeta", "Sepúlveda"]
    
    generos = ["Novela", "Poesía", "Ensayo", "Teatro", "Cuento", "Biografía", "Historia", "Filosofía"]
    
    titulos_extendidos = titulos.copy()
    
    # Generar más títulos combinando elementos
    for i in range(len(titulos), 1000):
        autor = random.choice(autores)
        genero = random.choice(generos)
        numero = random.randint(1, 10)
        titulo = f"{genero} de {autor} - Volumen {numero}"
        titulos_extendidos.append(titulo)
    
    return titulos_extendidos[:1000]

def generar_ejemplares_libro(libro_id, titulo, total_ejemplares):
    """Genera los ejemplares individuales para un libro"""
    ejemplares = []
    
    for i in range(total_ejemplares):
        ejemplar = {
            "ejemplar_id": f"{libro_id}-E{i+1:03d}",
            "libro_id": libro_id,
            "titulo": titulo,
            "estado": "disponible",  # disponible, prestado
            "fecha_devolucion": None,
            "usuario_prestamo": None,
            "sede": None
        }
        ejemplares.append(ejemplar)
    
    return ejemplares

def generar_datos_iniciales():
    """Genera la base de datos inicial completa"""
    print("Generando datos iniciales...")
    
    # Generar títulos
    titulos = generar_titulos_libros()
    
    # Crear estructura de datos
    libros = []
    ejemplares_totales = []
    
    # Contadores para libros prestados por sede
    prestados_sede_1 = 0
    prestados_sede_2 = 0
    
    for i, titulo in enumerate(titulos, 1):
        libro_id = f"L{i:04d}"
        
        # Determinar número de ejemplares (algunos libros tienen solo 1 ejemplar)
        if random.random() < 0.1:  # 10% de libros con 1 ejemplar
            total_ejemplares = 1
        else:
            total_ejemplares = random.randint(2, 15)  # Entre 2 y 15 ejemplares
        
        # Generar ejemplares
        ejemplares = generar_ejemplares_libro(libro_id, titulo, total_ejemplares)
        
        # Determinar cuántos ejemplares están prestados
        ejemplares_prestados = 0
        if i <= 200:  # Los primeros 200 libros tendrán ejemplares prestados
            if prestados_sede_1 < 50:
                ejemplares_prestados = min(random.randint(1, min(3, total_ejemplares)), 50 - prestados_sede_1)
                prestados_sede_1 += ejemplares_prestados
                sede_prestamo = "SEDE_1"
            elif prestados_sede_2 < 150:
                ejemplares_prestados = min(random.randint(1, min(3, total_ejemplares)), 150 - prestados_sede_2)
                prestados_sede_2 += ejemplares_prestados
                sede_prestamo = "SEDE_2"
            else:
                sede_prestamo = "SEDE_1"
        
        # Marcar ejemplares como prestados
        ejemplares_disponibles = total_ejemplares
        for j, ejemplar in enumerate(ejemplares):
            if j < ejemplares_prestados:
                ejemplar["estado"] = "prestado"
                ejemplar["sede"] = sede_prestamo
                ejemplar["usuario_prestamo"] = f"U{random.randint(1, 1000):04d}"
                # Fecha de devolución entre 1 y 30 días en el futuro
                dias_prestamo = random.randint(1, 30)
                fecha_devolucion = (datetime.now() + timedelta(days=dias_prestamo)).strftime('%Y-%m-%d')
                ejemplar["fecha_devolucion"] = fecha_devolucion
                ejemplares_disponibles -= 1
        
        # Crear entrada del libro
        libro = {
            "libro_id": libro_id,
            "titulo": titulo,
            "total_ejemplares": total_ejemplares,
            "ejemplares_disponibles": ejemplares_disponibles,
            "ejemplares_prestados": ejemplares_prestados,
            "ejemplares": ejemplares
        }
        
        libros.append(libro)
        ejemplares_totales.extend(ejemplares)
    
    # Crear estructura final
    base_datos = {
        "metadata": {
            "version": "1.0",
            "fecha_creacion": datetime.now().isoformat(),
            "total_libros": len(libros),
            "total_ejemplares": len(ejemplares_totales),
            "ejemplares_prestados_sede_1": prestados_sede_1,
            "ejemplares_prestados_sede_2": prestados_sede_2,
            "ejemplares_disponibles": len(ejemplares_totales) - prestados_sede_1 - prestados_sede_2
        },
        "libros": libros,
        "ejemplares": ejemplares_totales
    }
    
    return base_datos

def guardar_datos(base_datos, archivo="data/libros.json"):
    """Guarda los datos en el archivo JSON"""
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(archivo), exist_ok=True)
        
        # Crear backup del archivo existente
        if os.path.exists(archivo):
            backup_file = f"{archivo}.backup"
            import shutil
            shutil.copy2(archivo, backup_file)
            print(f"Backup creado: {backup_file}")
        
        # Guardar nuevos datos
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(base_datos, f, ensure_ascii=False, indent=2)
        
        print(f"Datos guardados en: {archivo}")
        return True
        
    except Exception as e:
        print(f"Error guardando datos: {e}")
        return False

def guardar_replicas(base_datos):
    """Guarda los datos en las réplicas primaria y secundaria"""
    import shutil
    
    # Guardar en archivo principal primero
    if not guardar_datos(base_datos, "data/libros.json"):
        return False
    
    # Crear directorios para réplicas
    os.makedirs("data/primary", exist_ok=True)
    os.makedirs("data/secondary", exist_ok=True)
    
    # Guardar en réplica primaria
    primary_path = "data/primary/libros.json"
    if not guardar_datos(base_datos, primary_path):
        print("Error guardando réplica primaria")
        return False
    
    # Copiar a réplica secundaria (idéntica a primaria)
    secondary_path = "data/secondary/libros.json"
    try:
        shutil.copy2(primary_path, secondary_path)
        print(f"Réplica secundaria creada: {secondary_path}")
    except Exception as e:
        print(f"Error copiando a réplica secundaria: {e}")
        return False
    
    print("✅ Réplicas primaria y secundaria inicializadas correctamente")
    return True

def mostrar_estadisticas(base_datos):
    """Muestra estadísticas de los datos generados"""
    metadata = base_datos["metadata"]
    
    print("\n" + "="*50)
    print("ESTADÍSTICAS DE DATOS INICIALES")
    print("="*50)
    print(f"Total de libros: {metadata['total_libros']}")
    print(f"Total de ejemplares: {metadata['total_ejemplares']}")
    print(f"Ejemplares disponibles: {metadata['ejemplares_disponibles']}")
    print(f"Ejemplares prestados en SEDE_1: {metadata['ejemplares_prestados_sede_1']}")
    print(f"Ejemplares prestados en SEDE_2: {metadata['ejemplares_prestados_sede_2']}")
    print(f"Total ejemplares prestados: {metadata['ejemplares_prestados_sede_1'] + metadata['ejemplares_prestados_sede_2']}")
    
    # Estadísticas adicionales
    libros_con_1_ejemplar = sum(1 for libro in base_datos["libros"] if libro["total_ejemplares"] == 1)
    print(f"Libros con 1 ejemplar: {libros_con_1_ejemplar}")
    
    print("="*50)

def main():
    """Función principal"""
    print("Generador de Datos Iniciales - Sistema de Préstamo de Libros")
    print("="*60)
    
    # Generar datos
    base_datos = generar_datos_iniciales()
    
    # Mostrar estadísticas
    mostrar_estadisticas(base_datos)
    
    # Guardar datos en réplicas primaria y secundaria
    if guardar_replicas(base_datos):
        print("\n✅ Datos iniciales generados exitosamente!")
        print("El sistema está listo para funcionar con los datos requeridos.")
        print("Réplicas primaria y secundaria sincronizadas.")
    else:
        print("\n❌ Error generando datos iniciales")

if __name__ == "__main__":
    main()
