"""
GA Storage module - Handles atomic read/write operations on books.json and loans.json.
Implements business logic for renovar, devolver, and checkAndLoan operations.
"""

import os
import json
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from common.time_utils import today_plus_days, add_days_to_date
from common.logging_utils import log_message


class GAStorage:
    """Thread-safe storage manager for books and loans data"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.books_file = os.path.join(data_dir, "books.json")
        self.loans_file = os.path.join(data_dir, "loans.json")
        self._lock = threading.RLock()
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize data files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize data files if they don't exist"""
        with self._lock:
            if not os.path.exists(self.books_file):
                self._write_json_file(self.books_file, [])
            
            if not os.path.exists(self.loans_file):
                self._write_json_file(self.loans_file, [])
    
    def _read_json_file(self, filepath: str) -> List[Dict]:
        """Read JSON file safely"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except (json.JSONDecodeError, IOError) as e:
            log_message("GA", "storage", "READ", "error", f"Error reading {filepath}: {str(e)}")
            return []
    
    def _write_json_file(self, filepath: str, data: List[Dict]):
        """Write JSON file atomically"""
        try:
            # Write to temporary file first
            temp_file = filepath + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            os.rename(temp_file, filepath)
        except IOError as e:
            log_message("GA", "storage", "WRITE", "error", f"Error writing {filepath}: {str(e)}")
            raise
    
    def _find_book(self, codigo: str) -> Optional[Dict]:
        """Find book by code"""
        books = self._read_json_file(self.books_file)
        for book in books:
            if book.get("codigo") == codigo:
                return book
        return None
    
    def _find_loan(self, codigo: str, userId: str) -> Optional[Dict]:
        """Find active loan by book code and user ID"""
        loans = self._read_json_file(self.loans_file)
        for loan in loans:
            if loan.get("codigo") == codigo and loan.get("userId") == userId:
                return loan
        return None
    
    def _update_book_availability(self, codigo: str, disponible: bool):
        """Update book availability"""
        books = self._read_json_file(self.books_file)
        for book in books:
            if book.get("codigo") == codigo:
                book["disponible"] = disponible
                break
        self._write_json_file(self.books_file, books)
    
    def _add_loan(self, codigo: str, userId: str, dueDate: str):
        """Add new loan"""
        loans = self._read_json_file(self.loans_file)
        new_loan = {
            "codigo": codigo,
            "userId": userId,
            "dueDate": dueDate,
            "renovaciones": 0
        }
        loans.append(new_loan)
        self._write_json_file(self.loans_file, loans)
    
    def _remove_loan(self, codigo: str, userId: str):
        """Remove loan"""
        loans = self._read_json_file(self.loans_file)
        loans = [loan for loan in loans if not (loan.get("codigo") == codigo and loan.get("userId") == userId)]
        self._write_json_file(self.loans_file, loans)
    
    def _update_loan_due_date(self, codigo: str, userId: str, new_due_date: str):
        """Update loan due date and increment renovations"""
        loans = self._read_json_file(self.loans_file)
        for loan in loans:
            if loan.get("codigo") == codigo and loan.get("userId") == userId:
                loan["dueDate"] = new_due_date
                loan["renovaciones"] = loan.get("renovaciones", 0) + 1
                break
        self._write_json_file(self.loans_file, loans)
    
    def renovar(self, id: str, codigo: str, userId: str, dueDateNew: str) -> Dict[str, Any]:
        """
        Renovate a loan.
        Business rules:
        - Book must be loaned to the user
        - Maximum 2 renovations per loan
        """
        with self._lock:
            try:
                # Find the loan
                loan = self._find_loan(codigo, userId)
                if not loan:
                    return {
                        "ok": False,
                        "reason": f"No active loan found for user {userId} and book {codigo}",
                        "metadata": None
                    }
                
                # Check renovation limit
                renovaciones = loan.get("renovaciones", 0)
                if renovaciones >= 2:
                    return {
                        "ok": False,
                        "reason": f"Maximum renovations (2) already reached for book {codigo}",
                        "metadata": None
                    }
                
                # Update loan
                self._update_loan_due_date(codigo, userId, dueDateNew)
                
                log_message("GA", id, "RENOVAR", "aplicado", 
                           f"Renovation successful for user {userId}, book {codigo}, new due date: {dueDateNew}")
                
                return {
                    "ok": True,
                    "reason": None,
                    "metadata": {"dueDate": dueDateNew, "renovaciones": renovaciones + 1}
                }
                
            except Exception as e:
                log_message("GA", id, "RENOVAR", "error", f"Error renovating loan: {str(e)}")
                return {
                    "ok": False,
                    "reason": f"Internal error: {str(e)}",
                    "metadata": None
                }
    
    def devolver(self, id: str, codigo: str, userId: str) -> Dict[str, Any]:
        """
        Return a book.
        Business rules:
        - Book must be loaned to the user
        - Mark book as available
        - Remove loan record
        """
        with self._lock:
            try:
                # Find the loan
                loan = self._find_loan(codigo, userId)
                if not loan:
                    return {
                        "ok": False,
                        "reason": f"No active loan found for user {userId} and book {codigo}",
                        "metadata": None
                    }
                
                # Mark book as available
                self._update_book_availability(codigo, True)
                
                # Remove loan
                self._remove_loan(codigo, userId)
                
                log_message("GA", id, "DEVOLVER", "aplicado", 
                           f"Return successful for user {userId}, book {codigo} now available")
                
                return {
                    "ok": True,
                    "reason": None,
                    "metadata": {"available": True}
                }
                
            except Exception as e:
                log_message("GA", id, "DEVOLVER", "error", f"Error returning book: {str(e)}")
                return {
                    "ok": False,
                    "reason": f"Internal error: {str(e)}",
                    "metadata": None
                }
    
    def checkAndLoan(self, id: str, codigo: str, userId: str) -> Dict[str, Any]:
        """
        Check availability and create loan if possible.
        Business rules:
        - Book must be available
        - Create loan with due date = today + 14 days
        - Mark book as unavailable
        """
        with self._lock:
            try:
                # Check if book exists and is available
                book = self._find_book(codigo)
                if not book:
                    return {
                        "ok": False,
                        "reason": f"Book {codigo} not found",
                        "metadata": None
                    }
                
                if not book.get("disponible", False):
                    return {
                        "ok": False,
                        "reason": f"Book {codigo} is not available",
                        "metadata": None
                    }
                
                # Check if user already has this book loaned
                existing_loan = self._find_loan(codigo, userId)
                if existing_loan:
                    return {
                        "ok": False,
                        "reason": f"User {userId} already has book {codigo} loaned",
                        "metadata": None
                    }
                
                # Create loan
                due_date = today_plus_days(14)
                self._add_loan(codigo, userId, due_date)
                
                # Mark book as unavailable
                self._update_book_availability(codigo, False)
                
                log_message("GA", id, "PRESTAR", "aplicado", 
                           f"Loan successful for user {userId}, book {codigo}, due date: {due_date}")
                
                return {
                    "ok": True,
                    "reason": None,
                    "metadata": {"dueDate": due_date}
                }
                
            except Exception as e:
                log_message("GA", id, "PRESTAR", "error", f"Error creating loan: {str(e)}")
                return {
                    "ok": False,
                    "reason": f"Internal error: {str(e)}",
                    "metadata": None
                }
    
    def get_books(self) -> List[Dict]:
        """Get all books"""
        with self._lock:
            return self._read_json_file(self.books_file)
    
    def get_loans(self) -> List[Dict]:
        """Get all loans"""
        with self._lock:
            return self._read_json_file(self.loans_file)
    
    def add_book(self, codigo: str, titulo: str, disponible: bool = True):
        """Add a new book"""
        with self._lock:
            books = self._read_json_file(self.books_file)
            new_book = {
                "codigo": codigo,
                "titulo": titulo,
                "disponible": disponible
            }
            books.append(new_book)
            self._write_json_file(self.books_file, books)
