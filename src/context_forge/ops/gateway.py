import os
from google import genai
from google.genai import types
from context_forge.core.state import ForgeState

def upload_to_gemini(state: ForgeState) -> ForgeState:
    """
    Step 3: Upload the merged XML to Gemini Context Cache.
    """
    if not state.is_valid: return state

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return state.fail("GOOGLE_API_KEY environment variable is not set.")

    state = state.add_log("☁️  Initializing Gemini Client...")
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Load the merged content
        if not state.merged_context_path:
             return state.fail("Merged context path is missing.")
             
        with open(state.merged_context_path, "r") as f:
            content_str = f.read()
            
        # Token Estimate (Rough char count / 4)
        est_tokens = len(content_str) // 4
        state = state.add_log(f"☁️  Uploading ~{est_tokens:,} tokens to Gemini 3 Cache...")

        # Create the explicit cache
        # We target the new Gemini 3 Ultra Preview model
        cache = client.caches.create(
            model="models/gemini-3-ultra-preview",
            config=types.CreateCachedContentConfig(
                display_name="ContextForge-QuantStack",
                system_instruction=(
                    "You are a Principal Quant Engineer. "
                    "You have read-only access to VectorBT Pro stubs and Lightweight Charts source. "
                    "You are working in the <workspace>."
                ),
                contents=[types.Content(
                    role="user",
                    parts=[types.Part(text=content_str)]
                )],
                # 8 Hour TTL (Workday)
                ttl="28800s" 
            )
        )
        
        return state.model_copy(update={
            "cache_name": cache.name,
            "cache_expire_time": str(cache.expire_time)
        })

    except Exception as e:
        return state.fail(f"Gemini API Error: {str(e)}")