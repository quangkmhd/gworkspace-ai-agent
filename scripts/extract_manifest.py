"""Extract tool manifest from docs/13. MCP TOOL MANIFEST.md into configs/tool_manifest.json."""
import re
import json
from pathlib import Path

root = Path(__file__).parent.parent
doc = root / "docs" / "13. MCP TOOL MANIFEST.md"
out = root / "configs" / "tool_manifest.json"

content = doc.read_text()
blocks = re.findall(r'```json\n(.*?)```', content, re.DOTALL)

for block in blocks:
    block = block.strip()
    try:
        data = json.loads(block)
        if "tools" in data:
            out.write_text(json.dumps(data, indent=2))
            print(f"OK: {len(data['tools'])} tools extracted to {out}")
            break
    except json.JSONDecodeError:
        continue
else:
    print("ERROR: No tools manifest found in doc")
