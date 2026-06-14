import asyncio
import os
import sys
from datetime import datetime, timezone

# Setup PYTHONPATH based on the script's directory
script_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(script_dir)
sys.path.append(os.path.join(script_dir, "eduquiz_bot"))

from sqlalchemy import select
from app.db.session import async_session
from app.db.models import AccessRequest, User, UserRole
from app.services.auth import get_user_by_tg_id, validate_access_password

async def test_auth():
    print("Simulating bot login for Test Teacher with limits...")
    async with async_session() as session:
        # 1. Validate password
        access = await validate_access_password(session, "L4uN4tz2")
        if not access:
            print("ERROR: Password validation failed.")
            return
            
        print(f"Success: Valid password for {access.full_name}, Limits: max_tests={access.max_tests}, max_students={access.max_students}, expires_at={access.expires_at}")
        
        # 2. Simulate handler code:
        # Check if user already exists
        user = await get_user_by_tg_id(session, 999999)
        if user:
            print(f"User already exists (Role: {user.role})")
            user.role = UserRole.TEACHER
            user.max_tests = access.max_tests
            user.max_students = access.max_students
            user.expires_at = access.expires_at
        else:
            print("Creating new User in database with limits...")
            user = User(
                tg_user_id=999999,
                full_name=access.full_name,
                role=UserRole.TEACHER,
                lang_code="uz",
                max_tests=access.max_tests,
                max_students=access.max_students,
                expires_at=access.expires_at
            )
            session.add(user)
            
        access.status = "used"
        await session.commit()
        print("Commit completed!")

    # Verify database state
    async with async_session() as session:
        user = await get_user_by_tg_id(session, 999999)
        print(f"Verified DB User: id={user.id}, tg_user_id={user.tg_user_id}, role={user.role}, max_tests={user.max_tests}, max_students={user.max_students}, expires_at={user.expires_at}, is_active={user.is_active}")
        
        # Check request status
        stmt = select(AccessRequest).where(AccessRequest.tg_user_id == 999999)
        res = await session.execute(stmt)
        req = res.scalar_one_or_none()
        print(f"Verified AccessRequest: status={req.status}")

if __name__ == "__main__":
    asyncio.run(test_auth())
