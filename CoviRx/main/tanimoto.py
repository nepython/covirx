from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem
from rdkit.rdBase import BlockLogs

block = BlockLogs() # Logs were blocked for better output
tanimoto_similarity_threshold = 0.7 # https://www.researchgate.net/post/Two_similar_compounds_with_a_low_smaller_than_085_Tanimoto_coefficient2


def get_molecules(drugs):
    drug_names, molecules = list(), list()
    for name, smile in drugs.items():
        # don't consider the drugs whose SMILES data is missing or is invalid
        if not smile:
            continue
        molecule = Chem.MolFromSmiles(smile)
        if not molecule:
            continue
        drug_names.append(name)
        molecules.append(molecule)
    return drug_names, molecules


def calculate_tanimoto_coefficients(ref_drugs, target_drug):
    target_name, t_molecule = get_molecules(target_drug)
    ref_names, r_molecules = get_molecules(ref_drugs)
    # Generate fingerprints from those molecules
    t_fingerprint = Chem.RDKFingerprint(t_molecule[0])
    r_fingerprints = list()
    for molecule in r_molecules:
        r_fingerprints.append(Chem.RDKFingerprint(molecule))
    tanimoto_coefficients = list()
    for i, r_fingerprint in enumerate(r_fingerprints):
        tanimoto_coefficient = round(DataStructs.TanimotoSimilarity(t_fingerprint, r_fingerprint), 3)
        tanimoto_coefficients.append(tanimoto_coefficient)
    return tanimoto_coefficients


def similar_drugs(ref_drugs, target_drug):
    """
    Args:
        drugs (dict): dict key gives the name of the drug and dict value gives its SMILES
        target_drug (dict): dict key gives the name of the drug and dict value gives its SMILES

    Returns:
        similar_drugs (dict): dict key gives the name of the drug and dict value gives similarity in percent
    """
    tanimoto_coefficients = calculate_tanimoto_coefficients(ref_drugs, target_drug)
    similar_drugs = dict()
    ref_drugs_names = list(ref_drugs.keys())
    for index, tanimoto in enumerate(tanimoto_coefficients):
        if float(tanimoto)<tanimoto_similarity_threshold:
            continue
        similar_drugs[ref_drugs_names[index]] = tanimoto
    return similar_drugs
