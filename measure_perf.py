
import asyncio
import os
import sys
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from main import generate_tax_return, TaxData

async def measure():
    print("--- Starting Performance Measurement ---")
    data = TaxData(
        full_name="Performance Test",
        ssn="000-00-0000",
        address="123 Speed St",
        city="Fastville",
        state="CA",
        zip_code="90210",
        wages=100000.0,
        federal_tax_withheld=20000.0,
        dividends=500.0,
        stock_gains=1000.0,
        days_present_2025=200,
        university="Speed University",
        entry_date="2024-01-01"
    )
    
    start = time.time()
    try:
        # generate_tax_return is async
        response = await generate_tax_return(data)
        
        # Consume the streaming response to ensure full execution
        content = b""
        async for chunk in response.body_iterator:
            content += chunk
            
        print(f"Total Response Size: {len(content)} bytes")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    print(f"--- End Measurement (Total Script Time: {time.time() - start:.4f}s) ---")

if __name__ == "__main__":
    asyncio.run(measure())
