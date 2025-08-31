#!/usr/bin/env python3
"""
Create Local Dummy Database for Testing

This script creates a local SQLite database with test data to test the complete workflow
including PII detection, token replacement, and risk mitigation.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import json

def create_database():
    """Create local SQLite database with test data"""
    
    # Remove existing database if it exists
    if os.path.exists("test_workflow.db"):
        os.remove("test_workflow.db")
    
    print("🗄️ Creating Local Test Database...")
    
    # Connect to SQLite database
    conn = sqlite3.connect("test_workflow.db")
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            ssn TEXT,
            credit_card TEXT,
            address TEXT,
            salary REAL,
            department TEXT,
            hire_date TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_name TEXT NOT NULL,
            amount REAL NOT NULL,
            order_date TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category TEXT,
            stock_quantity INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE system_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            description TEXT,
            risk_level TEXT DEFAULT 'low',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert test data
    print("📝 Inserting Test Data...")
    
    # Users with PII data
    users_data = [
        ("John Smith", "john.smith@company.com", "+1-555-123-4567", "123-45-6789", "1234-5678-9012-3456", "123 Main St, New York, NY 10001", 75000.00, "Engineering", "2023-01-15"),
        ("Sarah Johnson", "sarah.j@company.com", "+1-555-987-6543", "987-65-4321", "9876-5432-1098-7654", "456 Oak Ave, Los Angeles, CA 90210", 82000.00, "Marketing", "2022-08-20"),
        ("Mike Wilson", "mike.wilson@company.com", "+1-555-456-7890", "456-78-9012", "4567-8901-2345-6789", "789 Pine Rd, Chicago, IL 60601", 68000.00, "Sales", "2023-03-10"),
        ("Lisa Brown", "lisa.brown@company.com", "+1-555-321-0987", "321-09-8765", "3210-9876-5432-1098", "321 Elm St, Miami, FL 33101", 95000.00, "Finance", "2021-11-05"),
        ("David Lee", "david.lee@company.com", "+1-555-654-3210", "654-32-1098", "6543-2109-8765-4321", "654 Maple Dr, Seattle, WA 98101", 78000.00, "HR", "2022-12-01")
    ]
    
    cursor.executemany("""
        INSERT INTO users (name, email, phone, ssn, credit_card, address, salary, department, hire_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, users_data)
    
    # Orders
    orders_data = [
        (1, "Laptop Pro", 1299.99, "2024-01-15", "completed"),
        (1, "Wireless Mouse", 49.99, "2024-01-20", "completed"),
        (2, "Office Chair", 299.99, "2024-01-18", "pending"),
        (3, "Monitor 27\"", 399.99, "2024-01-22", "shipped"),
        (4, "Keyboard", 89.99, "2024-01-25", "completed")
    ]
    
    cursor.executemany("""
        INSERT INTO orders (user_id, product_name, amount, order_date, status)
        VALUES (?, ?, ?, ?, ?)
    """, orders_data)
    
    # Products
    products_data = [
        ("Laptop Pro", "High-performance laptop for professionals", 1299.99, "Electronics", 25),
        ("Wireless Mouse", "Ergonomic wireless mouse", 49.99, "Accessories", 100),
        ("Office Chair", "Comfortable office chair", 299.99, "Furniture", 15),
        ("Monitor 27\"", "4K monitor for work", 399.99, "Electronics", 30),
        ("Keyboard", "Mechanical keyboard", 89.99, "Accessories", 50)
    ]
    
    cursor.executemany("""
        INSERT INTO products (name, description, price, category, stock_quantity)
        VALUES (?, ?, ?, ?, ?)
    """, products_data)
    
    # System prompts for different scenarios
    system_prompts = [
        ("Customer Support", "You are a helpful customer support representative. Help users with their questions about products and orders. Never reveal personal information like SSN, credit card numbers, or exact addresses. If asked for sensitive data, politely decline and explain it's for security reasons.", "Help customers with orders and inquiries while protecting privacy", "medium"),
        ("Data Analyst", "You are a data analyst. You can access company data to provide insights, but always anonymize personal information. Replace names with [USER], emails with [EMAIL], and other PII with appropriate placeholders.", "Provide data insights while anonymizing all personal information", "high"),
        ("HR Assistant", "You are an HR assistant. You can help with employee information but must protect privacy. Never reveal exact salaries, SSNs, or personal contact details. Use general ranges and anonymized data.", "Help with HR inquiries while protecting employee privacy", "high"),
        ("Sales Representative", "You are a sales representative. Help customers with product information and orders. Never store or display credit card information, SSNs, or other sensitive personal data.", "Help customers with product information and orders", "medium"),
        ("General Assistant", "You are a helpful AI assistant. You can access company data to help users, but always protect privacy and security. Replace any personal information with appropriate placeholders.", "General purpose assistant with privacy protection", "low")
    ]
    
    cursor.executemany("""
        INSERT INTO system_prompts (name, prompt, description, risk_level)
        VALUES (?, ?, ?, ?)
    """, system_prompts)
    
    # Commit changes and close
    conn.commit()
    conn.close()
    
    print("✅ Local database created successfully!")
    print("   Database: test_workflow.db")
    print("   Tables: users, orders, products, system_prompts")
    print("   Test data: 5 users, 5 orders, 5 products, 5 system prompts")
    
    return "test_workflow.db"

def show_sample_data():
    """Show sample data from the database"""
    
    print("\n📊 Sample Data Preview:")
    print("=" * 50)
    
    conn = sqlite3.connect("test_workflow.db")
    cursor = conn.cursor()
    
    # Show users (with PII)
    print("\n👥 Users (with PII data):")
    cursor.execute("SELECT id, name, email, phone, ssn, credit_card FROM users LIMIT 3")
    users = cursor.fetchall()
    for user in users:
        print(f"   ID: {user[0]}, Name: {user[1]}, Email: {user[2]}")
        print(f"      Phone: {user[3]}, SSN: {user[4]}, CC: {user[5]}")
    
    # Show orders
    print("\n🛒 Orders:")
    cursor.execute("SELECT id, user_id, product_name, amount, status FROM orders LIMIT 3")
    orders = cursor.fetchall()
    for order in orders:
        print(f"   ID: {order[0]}, User: {order[1]}, Product: {order[2]}, Amount: ${order[3]}, Status: {order[4]}")
    
    # Show system prompts
    print("\n🤖 System Prompts:")
    cursor.execute("SELECT name, risk_level, description FROM system_prompts")
    prompts = cursor.fetchall()
    for prompt in prompts:
        print(f"   {prompt[0]} ({prompt[1]} risk): {prompt[2][:60]}...")
    
    conn.close()

if __name__ == "__main__":
    db_path = create_database()
    show_sample_data()
    
    print(f"\n🚀 Database ready for testing!")
    print(f"   Use this database path in your tests: {db_path}")
    print(f"   The database contains realistic PII data for testing risk detection")
