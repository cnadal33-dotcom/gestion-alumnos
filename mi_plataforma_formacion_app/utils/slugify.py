import unicodedata
import re

def slugify(value):
    value = str(value).strip().lower()
    value = unicodedata.normalize('NFKD', value)
    value = value.encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^a-z0-9]+', '_', value)
    value = re.sub(r'_+', '_', value)  # quita dobles guiones bajos
    return value.strip('_')
