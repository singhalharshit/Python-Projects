"""
Quick script to add the missing getter function to niche_discovery.py
"""

file_path = r"E:\Coding Practice\Python Projects\Python-Projects\Major Proj\backend\app\services\intelligence\niche_discovery.py"

# Read existing content
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add the getter function at the end
addition = """

# ✅ Global getter function
def get_niche_discovery(db: Session) -> NicheDiscoveryEngine:
    \"\"\"Get or create NicheDiscoveryEngine instance\"\"\"
    return NicheDiscoveryEngine(db)
"""

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content + addition)

print("✅ Added get_niche_discovery() function!")
