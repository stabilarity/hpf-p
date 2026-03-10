import re
import html as htmllib

# Read source mermaid blocks (ground truth)
with open('/root/hpf/chapter4_hpf_with_diagrams.md', 'r') as f:
    source = f.read()

source_blocks = re.findall(r'```mermaid\n(.*?)```', source, re.DOTALL)
print(f"Source blocks: {len(source_blocks)}", flush=True)

# Read WP HTML content
with open('/tmp/ch4_wp.html', 'r') as f:
    wp_content = f.read()

wp_blocks = re.findall(r'class="mermaid">(.*?)</pre>', wp_content, re.DOTALL)
print(f"WP blocks: {len(wp_blocks)}", flush=True)

def transform_mermaid(src_block):
    """Transform source markdown mermaid to WP-ready mermaid."""
    code = src_block
    
    # Replace \n inside quoted node labels with <br/>
    # Pattern: inside "..." replace \n with <br/>
    def replace_newlines_in_quotes(m):
        return m.group(0).replace('\\n', '<br/>')
    
    # Handle \n in double-quoted strings
    code = re.sub(r'"[^"]*\\n[^"]*"', replace_newlines_in_quotes, code)
    
    # For any remaining \n that are literal backslash-n (not inside quotes but might be in node labels)
    # Actually in source these ARE literal \n sequences
    # Let's be safe: replace all remaining \n sequences
    code = code.replace('\\n', '<br/>')
    
    return code

# Build replacement map
if len(source_blocks) != len(wp_blocks):
    print(f"WARNING: block count mismatch! source={len(source_blocks)} wp={len(wp_blocks)}")

# Replace each mermaid block in WP content with clean version from source
result = wp_content
offset = 0
wp_block_pattern = re.compile(r'(<pre[^>]*class="mermaid"[^>]*>)(.*?)(</pre>)', re.DOTALL)

matches = list(wp_block_pattern.finditer(result))
print(f"Found {len(matches)} pre.mermaid tags in WP", flush=True)

# Build new content by replacing blocks one by one
new_content = wp_content
replacements = []

for i, m in enumerate(matches):
    if i < len(source_blocks):
        clean = transform_mermaid(source_blocks[i])
        replacements.append((m.group(0), f'<pre class="mermaid">\n{clean}</pre>'))
    
# Apply replacements
for old, new in replacements:
    new_content = new_content.replace(old, new, 1)

with open('/tmp/ch4_fixed.html', 'w') as f:
    f.write(new_content)

print(f"Written /tmp/ch4_fixed.html ({len(new_content)} chars)", flush=True)

# Verify
fixed_blocks = re.findall(r'class="mermaid">(.*?)</pre>', new_content, re.DOTALL)
print(f"Fixed file has {len(fixed_blocks)} mermaid blocks", flush=True)

issues = 0
for i, b in enumerate(fixed_blocks):
    if '&quot;' in b:
        print(f"  Block {i+1}: still has &quot;")
        issues += 1
    # Check for literal-n issue: letter followed by n followed by uppercase/quote
    if re.search(r'[a-zA-Z]n[A-Z"•→\[]', b):
        print(f"  Block {i+1}: may still have literal-n issue")
        issues += 1
    if '\\n' in b:
        print(f"  Block {i+1}: still has backslash-n")
        issues += 1

print(f"Total issues: {issues}", flush=True)
