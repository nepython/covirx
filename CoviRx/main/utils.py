from collections import OrderedDict

searchfields = ['name', 'smiles', 'inchi', 'synonyms', 'cas', 'chebl', 'pubchem']

# It should be in lowecase with spaces replaced by underscore
verbose_names = {
    'indication_class/category': 'indication_class'
}

# Dictionary contains the list of all invalidated drugs during drug upload
invalid_drugs = OrderedDict()
