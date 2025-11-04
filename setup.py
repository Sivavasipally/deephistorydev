"""Setup script to initialize the application."""

import os
import shutil
from pathlib import Path


def setup():
    """Initialize the application."""
    print("=" * 60)
    print("Git History Deep Analyzer - Setup")
    print("=" * 60)

    # Check if .env exists
    env_path = Path('.env')
    env_example_path = Path('.env.example')

    if not env_path.exists():
        if env_example_path.exists():
            print("\n📝 Creating .env file from .env.example...")
            shutil.copy(env_example_path, env_path)
            print("✓ .env file created")
            print("\n⚠️  IMPORTANT: Edit .env file with your configuration")
            print("   - Set database type (sqlite or mariadb)")
            print("   - Add Git credentials for private repositories")
        else:
            print("\n❌ .env.example not found")
            return
    else:
        print("\n✓ .env file already exists")

    # Create directories
    print("\n📁 Creating directories...")
    dirs_to_create = ['repositories']

    for dir_name in dirs_to_create:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"✓ Created {dir_name}/")
        else:
            print(f"✓ {dir_name}/ already exists")

    # Check requirements
    print("\n📦 Checking dependencies...")
    print("Run: pip install -r requirements.txt")

    # Summary
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Prepare your CSV file with repositories")
    print("4. Run CLI: python cli.py your_repositories.csv")
    print("5. Launch dashboard: streamlit run dashboard.py")
    print("=" * 60)


if __name__ == '__main__':
    setup()
