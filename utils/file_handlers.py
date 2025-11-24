import os


class Tee:
    """Redirect stdout to both terminal and a file"""

    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()


def get_unique_filename(base_name, ext=".txt", folder="reports"):
    """
    Generate a unique filename like base_name.txt, base_name_2.txt, etc.
    Args:
        base_name: str of naming convention for file
        ext: str of file extension (default = ".txt")
        folder: name of folder to save reports to
    Return:
        str of file name
    """
    # Ensure the folder exists
    os.makedirs(folder, exist_ok=True)
    # Build the initial file path
    filename = os.path.join(folder, f"{base_name}{ext}")
    counter = 2
    while os.path.exists(filename):
        filename = os.path.join(folder, f"{base_name}_{counter}{ext}")
        counter += 1
    return filename
