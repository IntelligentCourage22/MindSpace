#!/usr/bin/env python
"""
Setup script for MindSpace backend
Run this script to set up the development environment
"""

import os
import sys
import subprocess
import django
from django.core.management import execute_from_command_line

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def setup_environment():
    """Set up the development environment"""
    print("🚀 Setting up MindSpace Backend...")
    
    # Check if virtual environment exists
    if not os.path.exists('venv'):
        print("📦 Creating virtual environment...")
        if not run_command('python -m venv venv', 'Creating virtual environment'):
            return False
    
    # Install requirements
    if not run_command('pip install -r requirements.txt', 'Installing Python dependencies'):
        return False
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindspace.settings')
    django.setup()
    
    # Run migrations
    if not run_command('python manage.py makemigrations', 'Creating database migrations'):
        return False
    
    if not run_command('python manage.py migrate', 'Running database migrations'):
        return False
    
    # Create superuser
    print("👤 Creating superuser...")
    print("You'll be prompted to enter username, email, and password for the admin user.")
    if not run_command('python manage.py createsuperuser', 'Creating superuser'):
        print("⚠️  Superuser creation failed. You can create one later with: python manage.py createsuperuser")
    
    # Seed demo data
    print("🌱 Seeding demo data...")
    if not run_command('python manage.py seed_data --users 10 --entries 30 --posts 20', 'Seeding demo data'):
        print("⚠️  Demo data seeding failed. You can run it later with: python manage.py seed_data")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Start the development server: python manage.py runserver")
    print("2. Visit http://localhost:8000/admin/ to access the admin panel")
    print("3. Visit http://localhost:8000/api/ to explore the API")
    print("4. Set up the frontend: cd ../frontend && npm install && npm start")
    
    return True

if __name__ == '__main__':
    if setup_environment():
        sys.exit(0)
    else:
        sys.exit(1)
