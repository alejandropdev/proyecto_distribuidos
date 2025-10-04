"""
Seed data generator for GA storage.
Generates initial books.json and loans.json files for testing.
"""

import os
import sys
import json
import random
import typer
from typing import List, Dict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.logging_utils import log_message
from common.time_utils import today_plus_days

app = typer.Typer()


def generate_books(count: int = 1000) -> List[Dict]:
    """Generate list of books"""
    books = []
    
    # Sample book titles
    titles = [
        "El Quijote", "Cien años de soledad", "1984", "Orgullo y prejuicio",
        "El señor de los anillos", "Harry Potter", "Dune", "Fahrenheit 451",
        "El código Da Vinci", "Los juegos del hambre", "El alquimista",
        "Crimen y castigo", "Anna Karenina", "Moby Dick", "Ulises",
        "En busca del tiempo perdido", "El gran Gatsby", "Matar a un ruiseñor",
        "El guardián entre el centeno", "Las aventuras de Huckleberry Finn",
        "Cien años de soledad", "Rayuela", "La casa de los espíritus",
        "Pedro Páramo", "El túnel", "La ciudad y los perros", "Conversación en La Catedral",
        "Los detectives salvajes", "2666", "El amor en los tiempos del cólera"
    ]
    
    # Sample authors
    authors = [
        "Miguel de Cervantes", "Gabriel García Márquez", "George Orwell", "Jane Austen",
        "J.R.R. Tolkien", "J.K. Rowling", "Frank Herbert", "Ray Bradbury",
        "Dan Brown", "Suzanne Collins", "Paulo Coelho", "Fyodor Dostoevsky",
        "Leo Tolstoy", "Herman Melville", "James Joyce", "Marcel Proust",
        "F. Scott Fitzgerald", "Harper Lee", "J.D. Salinger", "Mark Twain",
        "Julio Cortázar", "Isabel Allende", "Juan Rulfo", "Ernesto Sábato",
        "Mario Vargas Llosa", "Roberto Bolaño", "Carlos Fuentes"
    ]
    
    for i in range(count):
        book = {
            "codigo": f"ISBN-{i:04d}",
            "titulo": f"{random.choice(titles)} - {random.choice(authors)}",
            "disponible": random.choice([True, True, True, False])  # 75% available
        }
        books.append(book)
    
    return books


def generate_loans(books: List[Dict], site: str, count: int = 200) -> List[Dict]:
    """Generate initial loans for a site"""
    loans = []
    
    # Get unavailable books (already loaned)
    unavailable_books = [book for book in books if not book["disponible"]]
    
    # Generate loans for unavailable books
    for i, book in enumerate(unavailable_books[:count]):
        loan = {
            "codigo": book["codigo"],
            "userId": f"u-{random.randint(1, 100)}",
            "dueDate": today_plus_days(random.randint(-7, 14)),  # Some overdue, some current
            "renovaciones": random.randint(0, 2)  # 0-2 renovations
        }
        loans.append(loan)
    
    return loans


def create_oplog_structure() -> List[Dict]:
    """Create empty oplog structure"""
    return []


def create_applied_index_structure() -> Dict:
    """Create applied index structure"""
    return {
        "last_applied_index": -1,
        "applied_operations": []
    }


def seed_site_data(data_dir: str, site: str, books_count: int = 1000, loans_count: int = 200):
    """Seed data for a specific site"""
    
    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    # Generate books
    books = generate_books(books_count)
    
    # Adjust availability based on site
    if site == "A":
        # Site A: 50 loans (5% of books)
        loans_count = 50
    else:
        # Site B: 150 loans (15% of books)
        loans_count = 150
    
    # Mark some books as unavailable (loaned)
    random.shuffle(books)
    for i in range(loans_count):
        if i < len(books):
            books[i]["disponible"] = False
    
    # Generate loans
    loans = generate_loans(books, site, loans_count)
    
    # Write books.json
    books_file = os.path.join(data_dir, "books.json")
    with open(books_file, 'w', encoding='utf-8') as f:
        json.dump(books, f, indent=2, ensure_ascii=False)
    
    # Write loans.json
    loans_file = os.path.join(data_dir, "loans.json")
    with open(loans_file, 'w', encoding='utf-8') as f:
        json.dump(loans, f, indent=2, ensure_ascii=False)
    
    # Write oplog.json
    oplog_file = os.path.join(data_dir, "oplog.json")
    with open(oplog_file, 'w', encoding='utf-8') as f:
        json.dump(create_oplog_structure(), f, indent=2, ensure_ascii=False)
    
    # Write applied_index.json
    applied_index_file = os.path.join(data_dir, "applied_index.json")
    with open(applied_index_file, 'w', encoding='utf-8') as f:
        json.dump(create_applied_index_structure(), f, indent=2, ensure_ascii=False)
    
    print(f"✅ Seeded data for site {site}:")
    print(f"   📚 Books: {len(books)} ({sum(1 for b in books if b['disponible'])} available)")
    print(f"   📖 Loans: {len(loans)}")
    print(f"   📁 Data directory: {data_dir}")


@app.command()
def main(
    data_dir: str = typer.Option("./data/siteA", "--data-dir", help="Data directory to seed"),
    site: str = typer.Option("A", "--site", help="Site identifier (A or B)"),
    books_count: int = typer.Option(1000, "--books", help="Number of books to generate"),
    loans_count: int = typer.Option(200, "--loans", help="Number of initial loans")
):
    """Generate seed data for GA storage"""
    
    print(f"🌱 Generating seed data for site {site}...")
    
    try:
        seed_site_data(data_dir, site, books_count, loans_count)
        print("✅ Seed data generation completed successfully!")
        
    except Exception as e:
        print(f"❌ Error generating seed data: {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
