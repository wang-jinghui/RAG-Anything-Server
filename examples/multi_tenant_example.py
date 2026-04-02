"""
Example: Multi-tenant Knowledge Base Isolation

This example demonstrates how to use tenant_id and kb_id for multi-tenant isolation.
"""
import asyncio
from pathlib import Path
from raganything import RAGAnything
from raganything.config import RAGAnythingConfig


async def example_tenant_isolation():
    """Example 1: Using tenant_id for user-level isolation"""
    
    print("=" * 60)
    print("Example 1: Tenant-level Isolation")
    print("=" * 60)
    
    # Create RAGAnything instance with tenant_id
    # Each tenant gets isolated storage directories
    rag_tenant1 = RAGAnything(
        config=RAGAnythingConfig(working_dir="./rag_storage"),
        tenant_id="user_123",  # Tenant ID
        # llm_model_func=your_llm_func,  # Configure as needed
        # embedding_func=your_embedding_func,
    )
    
    # This will create directory: ./rag_storage/tenant_user_123/
    # All data for this tenant is stored separately
    
    # Process documents for tenant 1
    await rag_tenant1.process_document_complete(
        "document1.pdf",
        output_dir="./output"
    )
    
    # Query tenant 1's data
    result1 = await rag_tenant1.aquery("What is document1 about?")
    print(f"Tenant 1 Query Result: {result1}")
    
    # Create another tenant instance
    rag_tenant2 = RAGAnything(
        config=RAGAnythingConfig(working_dir="./rag_storage"),
        tenant_id="user_456",  # Different tenant
    )
    
    # This creates: ./rag_storage/tenant_user_456/
    # Completely isolated from tenant 1
    
    await rag_tenant2.process_document_complete(
        "document2.pdf",
        output_dir="./output"
    )
    
    # Query tenant 2's data (won't see tenant 1's data)
    result2 = await rag_tenant2.aquery("What is document2 about?")
    print(f"Tenant 2 Query Result: {result2}")


async def example_kb_isolation():
    """Example 2: Using kb_id for knowledge base-level isolation"""
    
    print("\n" + "=" * 60)
    print("Example 2: Knowledge Base-level Isolation")
    print("=" * 60)
    
    # User can have multiple isolated knowledge bases
    kb1_rag = RAGAnything(
        config=RAGAnythingConfig(working_dir="./rag_storage"),
        kb_id="kb_research_papers",  # KB for research papers
    )
    
    # Creates: ./rag_storage/kb_kb_research_papers/
    
    await kb1_rag.process_document_complete(
        "research_paper.pdf",
        output_dir="./output"
    )
    
    # Create another KB for the same user
    kb2_rag = RAGAnything(
        config=RAGAnythingConfig(working_dir="./rag_storage"),
        kb_id="kb_meeting_notes",  # KB for meeting notes
    )
    
    # Creates: ./rag_storage/kb_kb_meeting_notes/
    
    await kb2_rag.process_document_complete(
        "meeting_notes.docx",
        output_dir="./output"
    )
    
    # Query each KB separately
    paper_result = await kb1_rag.aquery("Summarize the research findings")
    meeting_result = await kb2_rag.aquery("What were the action items?")
    
    print(f"Research KB: {paper_result}")
    print(f"Meeting KB: {meeting_result}")


async def example_combined_isolation():
    """Example 3: Combined tenant + KB isolation"""
    
    print("\n" + "=" * 60)
    print("Example 3: Combined Tenant + KB Isolation")
    print("=" * 60)
    
    # Multi-tenant system where each tenant has multiple KBs
    # Priority: kb_id takes precedence over tenant_id
    
    rag = RAGAnything(
        config=RAGAnythingConfig(working_dir="./rag_storage"),
        tenant_id="org_abc",  # Organization/tenant
        kb_id="kb_hr_docs",   # HR department KB
    )
    
    # Creates: ./rag_storage/kb_kb_hr_docs/
    # Note: When both are provided, kb_id is used for namespace
    
    await rag.process_document_complete(
        "hr_policy.pdf",
        output_dir="./output"
    )
    
    result = await rag.aquery("What is the vacation policy?")
    print(f"HR KB Query: {result}")


async def example_backward_compatibility():
    """Example 4: Backward compatibility (no tenant/KB specified)"""
    
    print("\n" + "=" * 60)
    print("Example 4: Backward Compatibility (No Isolation)")
    print("=" * 60)
    
    # Existing code continues to work without changes
    # No tenant_id or kb_id = no namespace isolation
    
    rag = RAGAnything(
        config=RAGAnythingConfig(working_dir="./rag_storage"),
        # No tenant_id, no kb_id
    )
    
    # Uses default directory: ./rag_storage/
    
    await rag.process_document_complete(
        "shared_doc.pdf",
        output_dir="./output"
    )
    
    result = await rag.aquery("What is this document about?")
    print(f"Default KB Query: {result}")
    
    print("\nNote: This maintains backward compatibility with existing code!")


async def main():
    """Run all examples"""
    
    print("\n" + "=" * 60)
    print("Multi-Tenant RAGAnything Examples")
    print("=" * 60)
    
    try:
        # Run examples
        await example_tenant_isolation()
        await example_kb_isolation()
        await example_combined_isolation()
        await example_backward_compatibility()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("\nNote: These examples show the API structure.")
        print("To run them, you need to configure:")
        print("  1. LLM model function")
        print("  2. Embedding function")
        print("  3. LightRAG storage backends")
        print("  4. Actual document files")


if __name__ == "__main__":
    asyncio.run(main())
