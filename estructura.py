import os

def tree(directory, prefix=''):
    """Devuelve la estructura de carpetas y archivos como string."""
    entries = sorted(os.listdir(directory))
    lines = []
    for i, entry in enumerate(entries):
        path = os.path.join(directory, entry)
        connector = "└── " if i == len(entries) - 1 else "├── "
        lines.append(prefix + connector + entry)
        if os.path.isdir(path):
            extension = "    " if i == len(entries) - 1 else "│   "
            lines += tree(path, prefix + extension)
    return lines

if __name__ == "__main__":
    raiz = os.path.dirname(os.path.abspath(__file__))
    estructura = [os.path.basename(raiz) + "/"]
    estructura += tree(raiz)
    with open("estructura.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(estructura))
    print("Archivo 'estructura.txt' generado correctamente.")
