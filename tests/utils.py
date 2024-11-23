def load_yaml(path):
    """Load YAML file and return its contents."""
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


def get_all_files_in_tree(node):
    """Get all file and directory names in the tree."""
    files = [node["name"]]
    if "children" in node:
        for child in node["children"]:
            files.extend(get_all_files_in_tree(child))
    return files
