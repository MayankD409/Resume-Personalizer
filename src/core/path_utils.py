from slugify import slugify # Function to create URL-friendly/filesystem-friendly strings
import pathlib # Module for object-oriented filesystem paths

def prepare_output_dir(base_output: str, company: str, role: str) -> pathlib.Path:
    """
    This function takes a base output directory, company name, and a role name,
    creates filesystem-safe versions of them, constructs a nested directory path 
    (base_output/company/role), ensures this directory exists, and returns the path object.
    """
    safe_company = slugify(company) # "DeepMind Inc." → "deepmind-inc"
    safe_role = slugify(role)      # "AI Engineer" → "ai-engineer"
    out_dir = pathlib.Path(base_output) / safe_company / safe_role
    out_dir.mkdir(parents=True, exist_ok=True)

    return out_dir