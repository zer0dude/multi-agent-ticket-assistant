#!/usr/bin/env python3
"""
Ticket Embedding Generation Utility

Generates OpenAI embeddings for all tickets in tickets.jsonl and saves them
in a structured format for future similarity search operations.
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add app to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.core.llm_client import LLMClient
from app.core.data import DataLoader

class TicketEmbeddingGenerator:
    """Utility class for generating and managing ticket embeddings"""
    
    def __init__(self, embeddings_file: str = "data/ticket_embeddings.json"):
        self.embeddings_file = Path(embeddings_file)
        self.client = LLMClient(provider="openai")  # Use OpenAI for embeddings
        self.data_loader = DataLoader()
        
    def load_existing_embeddings(self) -> Dict[str, Any]:
        """Load existing embeddings file or create empty structure"""
        if self.embeddings_file.exists():
            try:
                with open(self.embeddings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading existing embeddings: {e}")
                print("   Creating new embeddings file...")
        
        return {
            "metadata": {
                "model": "text-embedding-3-small",
                "dimension": 1536,
                "generated_at": datetime.now().isoformat(),
                "version": "1.0"
            },
            "embeddings": []
        }
    
    def create_embedding_content(self, ticket) -> str:
        """Create comprehensive content string for embedding"""
        content_parts = [
            f"Title: {ticket.title}",
            f"Body: {ticket.body}"
        ]
        
        # Add resolution if available (for closed tickets)
        if hasattr(ticket, 'resolution') and ticket.resolution:
            content_parts.append(f"Resolution: {ticket.resolution}")
        
        # Add related product SKUs for context
        if ticket.related_skus:
            content_parts.append(f"Related Products: {', '.join(ticket.related_skus)}")
            
        return "\n\n".join(content_parts)
    
    def create_content_hash(self, content: str) -> str:
        """Create SHA-256 hash of content for change detection"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def should_update_embedding(self, ticket_id: str, content_hash: str, existing_embeddings: Dict) -> bool:
        """Check if embedding needs to be updated"""
        for embedding in existing_embeddings.get("embeddings", []):
            if embedding.get("ticket_id") == ticket_id:
                return embedding.get("content_hash") != content_hash
        return True  # New ticket, needs embedding
    
    def generate_embeddings(self, force_regenerate: bool = False) -> Dict[str, Any]:
        """Generate embeddings for all tickets"""
        print("🎯 Starting ticket embedding generation...")
        
        # Load existing embeddings and tickets
        existing_data = self.load_existing_embeddings()
        tickets = self.data_loader.load_tickets()
        
        print(f"📄 Found {len(tickets)} tickets to process")
        
        # Track processing stats
        stats = {
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "total_tokens": 0
        }
        
        updated_embeddings = []
        existing_embeddings = {e["ticket_id"]: e for e in existing_data.get("embeddings", [])}
        
        for i, ticket in enumerate(tickets, 1):
            print(f"\n📋 Processing ticket {i}/{len(tickets)}: {ticket.ticket_id}")
            
            # Create embedding content
            content = self.create_embedding_content(ticket)
            content_hash = self.create_content_hash(content)
            
            # Check if update needed
            if not force_regenerate and not self.should_update_embedding(
                ticket.ticket_id, content_hash, existing_data
            ):
                print(f"   ✅ Using existing embedding (content unchanged)")
                updated_embeddings.append(existing_embeddings[ticket.ticket_id])
                stats["skipped"] += 1
                continue
            
            # Generate new embedding
            try:
                print(f"   🔄 Generating embedding...")
                print(f"   📝 Content preview: {content[:100]}...")
                
                embedding = self.client.get_embedding(content)
                
                # Verify embedding quality
                if len(embedding) != 1536:
                    raise ValueError(f"Unexpected embedding dimension: {len(embedding)}")
                
                # Create embedding record
                embedding_record = {
                    "ticket_id": ticket.ticket_id,
                    "content_hash": content_hash,
                    "embedding": embedding,
                    "content_preview": content[:200] + "..." if len(content) > 200 else content,
                    "generated_at": datetime.now().isoformat(),
                    "token_count": len(content.split())  # Rough estimate
                }
                
                updated_embeddings.append(embedding_record)
                stats["processed"] += 1
                stats["total_tokens"] += embedding_record["token_count"]
                
                print(f"   ✅ Embedding generated ({len(embedding)} dimensions)")
                
            except Exception as e:
                print(f"   ❌ Failed to generate embedding: {e}")
                # Keep existing embedding if available
                if ticket.ticket_id in existing_embeddings:
                    print(f"   🔄 Using existing embedding as fallback")
                    updated_embeddings.append(existing_embeddings[ticket.ticket_id])
                stats["errors"] += 1
        
        # Update metadata
        result_data = {
            "metadata": {
                "model": "text-embedding-3-small",
                "dimension": 1536,
                "generated_at": datetime.now().isoformat(),
                "version": "1.0",
                "total_tickets": len(tickets),
                "processing_stats": stats
            },
            "embeddings": updated_embeddings
        }
        
        return result_data
    
    def save_embeddings(self, embeddings_data: Dict[str, Any]):
        """Save embeddings to file with backup"""
        # Create backup if file exists
        if self.embeddings_file.exists():
            backup_file = self.embeddings_file.with_suffix('.json.backup')
            print(f"📄 Creating backup: {backup_file}")
            with open(self.embeddings_file, 'r') as src, open(backup_file, 'w') as dst:
                dst.write(src.read())
        
        # Ensure directory exists
        self.embeddings_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save embeddings
        with open(self.embeddings_file, 'w', encoding='utf-8') as f:
            json.dump(embeddings_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Embeddings saved to: {self.embeddings_file}")
    
    def validate_embeddings(self, embeddings_data: Dict[str, Any]) -> bool:
        """Validate generated embeddings"""
        print("🔍 Validating embeddings...")
        
        embeddings = embeddings_data.get("embeddings", [])
        if not embeddings:
            print("❌ No embeddings found")
            return False
        
        # Check dimensions
        expected_dim = embeddings_data["metadata"]["dimension"]
        for embedding in embeddings:
            if len(embedding["embedding"]) != expected_dim:
                print(f"❌ Invalid dimension for {embedding['ticket_id']}")
                return False
        
        print(f"✅ All {len(embeddings)} embeddings validated")
        return True
    
    def print_summary(self, embeddings_data: Dict[str, Any]):
        """Print generation summary"""
        metadata = embeddings_data["metadata"]
        stats = metadata.get("processing_stats", {})
        
        print(f"\n{'='*60}")
        print("EMBEDDING GENERATION SUMMARY")
        print(f"{'='*60}")
        print(f"📄 Total tickets: {metadata['total_tickets']}")
        print(f"✅ Processed: {stats.get('processed', 0)}")
        print(f"⏭️  Skipped (unchanged): {stats.get('skipped', 0)}")
        print(f"❌ Errors: {stats.get('errors', 0)}")
        print(f"🔤 Estimated tokens: {stats.get('total_tokens', 0)}")
        print(f"📐 Embedding model: {metadata['model']}")
        print(f"📏 Dimensions: {metadata['dimension']}")
        print(f"💾 Saved to: {self.embeddings_file}")
        
        # Cost estimation (rough)
        estimated_cost = (stats.get('total_tokens', 0) / 1000) * 0.00002  # $0.00002 per 1K tokens
        print(f"💰 Estimated cost: ${estimated_cost:.4f}")

def main():
    """Main function"""
    print("🚀 Ticket Embedding Generator")
    print("=" * 50)
    
    generator = TicketEmbeddingGenerator()
    
    # Check if LLM client is working
    info = generator.client.get_provider_info()
    print(f"🤖 Using provider: {info['primary_provider']}")
    print(f"📡 OpenAI available: {info['openai_available']}")
    print(f"🔤 Embedding model: {info['embedding_model']}")
    
    if not info['openai_available']:
        print("❌ OpenAI client not available! Cannot generate embeddings.")
        return
    
    # Generate embeddings
    try:
        embeddings_data = generator.generate_embeddings(force_regenerate=False)
        
        # Validate results
        if generator.validate_embeddings(embeddings_data):
            # Save to file
            generator.save_embeddings(embeddings_data)
            
            # Print summary
            generator.print_summary(embeddings_data)
            
            print(f"\n🎉 Embedding generation completed successfully!")
        else:
            print(f"\n❌ Validation failed. Embeddings not saved.")
            
    except Exception as e:
        print(f"\n💥 Fatal error during generation: {e}")
        return
    
    print(f"\n📚 Usage:")
    print(f"   The embeddings are now available at: {generator.embeddings_file}")
    print(f"   Use them for similarity search in your research workflows!")

if __name__ == "__main__":
    main()
