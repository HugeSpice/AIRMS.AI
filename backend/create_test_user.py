#!/usr/bin/env python3
"""
Create Test User in Supabase Database

This script creates a test user in the Supabase database for testing the authentication system.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import db
from app.core.auth import auth_manager

async def create_test_user():
    """Create a test user in Supabase"""
    
    print("🔐 Creating Test User in Supabase...")
    
    try:
        # Check if test user already exists
        existing_user = await db.get_user_by_email("admin@airms.com")
        
        if existing_user:
            print("✅ Test user already exists:")
            print(f"   Email: {existing_user['email']}")
            print(f"   ID: {existing_user['id']}")
            print(f"   Full Name: {existing_user.get('full_name', 'N/A')}")
            return
        
        # Hash password
        hashed_password = auth_manager.hash_password("admin123")
        
        # Create test user
        user_data = {
            "email": "admin@airms.com",
            "hashed_password": hashed_password,
            "full_name": "Admin User",
            "is_active": True,
            "is_verified": True
        }
        
        # Create user in Supabase
        user = await db.create_user(
            email=user_data["email"],
            hashed_password=user_data["hashed_password"],
            full_name=user_data["full_name"]
        )
        
        print("✅ Test user created successfully:")
        print(f"   Email: {user['email']}")
        print(f"   ID: {user['id']}")
        print(f"   Full Name: {user['full_name']}")
        print("\n📋 Login Credentials:")
        print(f"   Email: admin@airms.com")
        print(f"   Password: admin123")
        
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_test_user())
