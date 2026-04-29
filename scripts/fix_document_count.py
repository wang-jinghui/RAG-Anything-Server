"""
Fix document_count for all knowledge bases.

This script recalculates the document_count based on actual completed documents.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from server.models.database import Base
from server.models.knowledge_base import KnowledgeBase
from server.models.kb_document import KBDocument
from server.config import settings


async def fix_document_counts():
    """Recalculate document_count for all knowledge bases."""
    
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )
    
    # Create session factory
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    try:
        async with async_session() as db:
            # Get all knowledge bases
            result = await db.execute(select(KnowledgeBase))
            kbs = result.scalars().all()
            
            print(f"Found {len(kbs)} knowledge bases")
            print("=" * 80)
            
            for kb in kbs:
                # Count completed documents
                count_result = await db.execute(
                    select(func.count())
                    .select_from(KBDocument)
                    .where(
                        KBDocument.knowledge_base_id == kb.id,
                        KBDocument.upload_status == "completed"
                    )
                )
                actual_count = count_result.scalar()
                
                if kb.document_count != actual_count:
                    print(f"KB: {kb.name}")
                    print(f"  ID: {kb.id}")
                    print(f"  Old count: {kb.document_count}")
                    print(f"  New count: {actual_count}")
                    
                    kb.document_count = actual_count
                    await db.commit()
                    print(f"  ✓ Updated\n")
                else:
                    print(f"KB: {kb.name} - Count OK ({actual_count})\n")
            
            print("=" * 80)
            print("All knowledge bases updated!")
            
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("Fixing document counts for all knowledge bases...")
    print()
    asyncio.run(fix_document_counts())
