"""
Script to create initial super admin user.

Usage:
    python scripts/create_super_admin.py admin@example.com admin_username securepassword123
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import select

# Add parent directory to path
sys.path.insert(0, '.')

from server.models.database import Base
from server.models.user import User
from server.services.auth_service import get_password_hash


async def create_super_admin(email: str, username: str, password: str):
    """Create a super admin user."""
    
    # Create engine and tables
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/raganything",
        echo=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    async_session_maker = async_sessionmaker(engine, class_=User, expire_on_commit=False)
    
    async with async_session_maker() as db:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"❌ User with email {email} already exists!")
            return False
        
        # Check if username already exists
        result = await db.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"❌ Username {username} is already taken!")
            return False
        
        # Create super admin
        admin = User(
            email=email,
            username=username,
            password_hash=get_password_hash(password),
            is_super_admin=True,
            is_active=True
        )
        
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        
        print(f"✅ Super admin created successfully!")
        print(f"   Email: {admin.email}")
        print(f"   Username: {admin.username}")
        print(f"   ID: {admin.id}")
        print(f"\n🔐 You can now login and create knowledge bases.")
        print(f"📝 Login endpoint: POST /api/v1/auth/login")
        
        return True


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python scripts/create_super_admin.py <email> <username> <password>")
        print("\nExample:")
        print("  python scripts/create_super_admin.py admin@example.com admin securepassword123")
        sys.exit(1)
    
    email = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    # Validate password length
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long")
        sys.exit(1)
    
    # Run the async function
    success = asyncio.run(create_super_admin(email, username, password))
    sys.exit(0 if success else 1)
