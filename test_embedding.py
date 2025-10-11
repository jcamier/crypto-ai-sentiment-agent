"""Quick test of EmbeddingService"""
import sys
sys.path.insert(0, '/app')

from src.services.embedding_service import EmbeddingService

print("Testing EmbeddingService...")
print("=" * 50)

try:
    # Initialize service
    service = EmbeddingService()
    print("✓ Service initialized")
    
    # Test with a simple text
    test_text = "Bitcoin price reaches new all-time high as institutional adoption increases"
    print(f"\nTest text: {test_text[:50]}...")
    
    # Generate embedding
    embedding = service.generate_embedding(test_text)
    
    if embedding and len(embedding) > 0:
        print(f"✓ Embedding generated: {len(embedding)} dimensions")
        print(f"✓ First 5 values: {embedding[:5]}")
        
        # Check if it's not all zeros (would indicate fallback)
        if sum(embedding) != 0:
            print("✓ Embedding has non-zero values (real embedding)")
        else:
            print("⚠ Embedding is all zeros (fallback - check AWS credentials)")
    else:
        print("✗ Failed to generate embedding")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
