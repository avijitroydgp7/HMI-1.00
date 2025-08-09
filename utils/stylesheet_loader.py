import os
import logging
import re

# Configure logger for this module
logger = logging.getLogger(__name__)

def get_available_themes(styles_dir="styles"):
    """Scans the styles directory for theme subdirectories."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        styles_path = os.path.join(base_dir, styles_dir)
        
        if not os.path.isdir(styles_path):
            logger.debug(f"Styles directory not found: {styles_path}")
            return []
        
        themes = [d for d in os.listdir(styles_path) 
                 if os.path.isdir(os.path.join(styles_path, d)) and d.strip()]
        return sorted(themes)
    except Exception as e:
        logger.debug(f"Could not scan for themes: {e}")
        return []

def parse_variables(variables_path):
    """Parse CSS variables from variables.qss file."""
    variables = {}
    try:
        if not os.path.isfile(variables_path):
            return variables
            
        with open(variables_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse CSS custom properties
        pattern = r'--([a-zA-Z0-9\-_]+)\s*:\s*([^;]+);'
        matches = re.findall(pattern, content)
        
        for var_name, var_value in matches:
            variables[f'--{var_name}'] = var_value.strip()
            
    except Exception as e:
        logger.debug(f"Could not parse variables: {e}")
        
    return variables

def replace_variables(content, variables):
    """Replace CSS variable references with actual values."""
    if not variables:
        return content
        
    processed = content
    
    # Replace var(--variable-name) with actual values
    for var_name, var_value in variables.items():
        pattern = re.escape(f'var({var_name})')
        processed = re.sub(pattern, var_value, processed)
        
    return processed

def load_all_stylesheets(theme_name, styles_dir="styles"):
    """Loads and processes all .qss files with CSS variable replacement."""
    if not theme_name or not theme_name.strip():
        return ""

    full_stylesheet = ""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        theme_path = os.path.join(base_dir, styles_dir, theme_name)
        
        if not os.path.isdir(theme_path):
            return ""

        # Parse variables from variables.qss
        variables_path = os.path.join(theme_path, "variables.qss")
        variables = parse_variables(variables_path)
        
        # Load files alphabetically
        files = sorted([f for f in os.listdir(theme_path) 
                       if f.endswith(".qss") and os.path.isfile(os.path.join(theme_path, f))])

        # Process priority files first
        priority_files = ["global_fix.qss", "variables.qss"]
        for priority_file in priority_files:
            if priority_file in files:
                files.remove(priority_file)
                files.insert(0, priority_file)

        # Skip variables.qss as it's already processed
        files = [f for f in files if f != "variables.qss"]

        for file_name in files:
            full_path = os.path.join(theme_path, file_name)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        processed_content = replace_variables(content, variables)
                        full_stylesheet += processed_content + "\n"
            except Exception as e:
                logger.debug(f"Could not process file {file_name}: {e}")
        
        return full_stylesheet
    except Exception as e:
        logger.debug(f"Could not load stylesheets: {e}")
        return ""
