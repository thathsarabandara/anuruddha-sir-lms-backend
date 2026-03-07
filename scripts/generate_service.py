import os
import sys

# Mock dependencies
code_mocks = """
import sys
from unittest.mock import MagicMock
sys.modules['alembic'] = MagicMock()
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['sqlalchemy.sql'] = MagicMock()
op = MagicMock()
sa = MagicMock()
column = MagicMock()
table = MagicMock()
"""

def generate_service_code(nt001_path):
    with open(nt001_path, 'r') as f:
        content = f.read()
    
    # We only need the list of templates and variables from one file (assuming types match across channels)
    # nt001 seems to have the master list.
    
    scope = {}
    exec(code_mocks, scope)
    exec(content, scope) # nt001 doesn't use _build_html in _templates
    
    templates = scope['_templates']()
    
    code = []
    code.append("    # Auto-generated methods based on migration templates")
    
    for t in templates:
        t_type = t['notification_type']
        raw_vars = t.get('variables', [])
        
        # Filter out recipient_name etc if handled by base, but user wants specific signature? 
        # Pythonic: def send_x(self, user_id, var1, var2):
        
        # Clean vars: remove duplicates, sort
        vars_list = sorted(list(set(raw_vars)))
        
        # recipient_name is common, maybe pass it?
        # We'll generate kwargs based on variables
        
        args_str = ", ".join(vars_list)
        if args_str:
            args_str = ", " + args_str
            
        method_name = f"send_{t_type}"
        
        method = f"""
    def {method_name}(self, user_id{args_str}):
        \"\"\"
        Send {t_type} notification.
        Variables: {', '.join(vars_list)}
        \"\"\"
        variables = {{
"""
        for v in vars_list:
            method += f"            '{v}': {v},\n"
        
        method += f"""        }}
        return self._send_notification('{t_type}', user_id, variables)
"""
        code.append(method)
        
    return "\n".join(code)

if __name__ == '__main__':
    base_path = "/home/thathsara-bandara/Desktop/Thathsara/CV - Projects/anuruddha sir/lms-backend-new/anu-backend-flask"
    code = generate_service_code(os.path.join(base_path, "migrations/versions/nt001_email_notification_templates.py"))
    
    with open(os.path.join(base_path, "app/services/notifications/generated_methods.py"), 'w') as f:
        f.write(code)
    print("Done")
