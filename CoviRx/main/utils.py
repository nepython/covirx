from collections import OrderedDict

from .models import Drug

# Fields to be used to search on home page
search_fields = ['name', 'smiles', 'inchi', 'synonyms', 'cas', 'chebl', 'pubchem']

# Fields which have been name differently in excel sheet and in our Drug model
# It should be in lowercase with spaces replaced by underscore
verbose_names = {
    'indication': 'indication_class'
}

# Fields that need to be stored during a bulk drug upload
ignore_fields = ['id'] + list(verbose_names.values())
store_fields = [f.name for f in Drug._meta.get_fields() if f.name not in ignore_fields]

# Dictionary contains the list of all invalidated drugs during drug upload
invalid_drugs = OrderedDict()
