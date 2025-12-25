# Quick Reference: force_json Interface

## Usage in Backend

### Correct Usage (Now Supported)
```python
# Standard text generation
text = gemini.generate(prompt, temperature=0.7, max_tokens=300, force_json=False)

# Structured JSON generation with schema
json_str = gemini.generate(prompt, temperature=0.7, max_tokens=800, force_json=True)
```

### Persona Methods (Auto-handle retries)
```python
# MKBHD style (calm, professional)
text, intent = gemini.generate_mkbhd_script(prompt, temperature=0.6, max_tokens=1500)

# iJustine style (energetic, excited)
text, intent = gemini.generate_ijustine_script(prompt, temperature=0.8, max_tokens=1500)

# Generic with intent
text, intent = gemini.generate_with_intent(prompt, temperature=0.7, max_tokens=800)
```

## Retry Flow

Each persona method uses this 2-attempt strategy:

```
Attempt 1: JSON mode (force_json=True)
    ↓ success → return (text, intent)
    ↓ failure
    
Attempt 2: Simplified prompt (force_json=False)
    ↓ success → return (text, intent)
    ↓ failure
    
Fallback: Simple intent (create_simple_intent)
    → Always succeeds, never crashes
```

## Response Handling

### Formats Supported
- Plain JSON: `{"segments": [...]}`
- Fenced: ` ```json\n{...}\n``` `
- With preamble: `"Here's the output:\n{...}"`
- With trailing: `"{...}\n\nHope this helps!"`

### Incomplete Responses (Handled Gracefully)
- Just fence: `"```json"` → Detected, triggers retry
- Empty fence: `"```json\n\n```"` → Detected, triggers retry
- Missing segments: `{"total_duration": 10}` → Validated, triggers retry
- Empty segments: `{"segments": []}` → Validated, triggers retry

## Logging Output

### When force_json=True
```
[Gemini] JSON mode enabled (model=gemini-2.5-flash, tokens=800)
[Gemini] JSON response length: 456 chars
[Gemini] Response preview: {"segments":[{"text":"First segment"...
```

### On Success
```
[Gemini:MKBHD] ✓ Script generated (8 segments)
```

### On Retry
```
[Gemini:MKBHD] Attempt 1 failed: JSON extraction failed. Response length: 8, preview: ```json
[Gemini:MKBHD] Retry with simplified prompt
[Gemini:MKBHD] ✓ Script generated via retry (10 segments)
```

### On Fallback
```
[Gemini:MKBHD] Attempt 2 failed: ...
[Gemini:MKBHD] Both attempts failed, falling back to generic intent generator
```

## Testing

### Run Intent Parsing Tests
```bash
cd /mnt/d/Hack-051_HackX
source .venv-wsl/bin/activate
python tools/test_intent_parsing.py
```
Expected: `✓ ALL TESTS PASSED!`

### Run Interface Tests
```bash
python tools/test_gemini_interface.py
```
Expected: `✓ ALL INTERFACE TESTS PASSED!`

## Troubleshooting

### Issue: TypeError about force_json
**Cause**: Old version of gemini_client.py  
**Fix**: Ensure changes from Dec 25, 2025 are applied

### Issue: Gemini returns incomplete JSON
**Cause**: API quota exhausted  
**Behavior**: Now handled gracefully - triggers retry, then fallback  
**Solution**: Wait for quota reset or create new Google Cloud project

### Issue: Parse fails on valid JSON
**Check**: Ensure segments field exists and is non-empty  
**Check**: Run `tools/test_intent_parsing.py` to verify parser

## Key Files

- `ai/gemini_client.py`: Core client with force_json support
- `ai/script_intent.py`: Intent schema and parsing
- `backend/routes/generation.py`: Backend endpoints using client
- `tools/test_intent_parsing.py`: Parser robustness tests
- `tools/test_gemini_interface.py`: Interface compatibility tests
