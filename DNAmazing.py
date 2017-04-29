from collections import namedtuple, Counter
import json
# pronto OBO format parser
from pronto.parser import OboParser
from pronto.parser.obo import Relationship


SAMRecord = namedtuple(
    'SAMRecord',
    'qname flag rname pos mapq cigar rnext pnext tlen seq qual')


class SAMFile(object):
    '''
    Wrapper for SAM file (just a tab delimited file really)
    '''
    def __init__(self, fn):
        self._fn = fn
        self._file = open(fn)

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            record = next(self._file)
            # skip header lines
            if not record.startswith('@'):
                break
        record = record.split('\t')[:11]
        record[1] = int(record[1])
        record[3] = int(record[3])
        record[4] = int(record[4])
        record[7] = int(record[7])
        record[8] = int(record[8])
        return SAMRecord(*record)

    def close(self):
        self._file.close()


class AROJSON(object):
    '''
    A wrapper for the OBO and JSON Antibiotic Resistance Ontology (ARO) format.
    '''
    def __init__(self, json_fn, obo_fn):
        self._json_fn = json_fn
        self._obo_fn = obo_fn
        with open(json_fn) as f:
            self._aro = json.load(f)
            self._aro = {x.pop('accession'): x for x in self._aro}
        with open(obo_fn, 'rb') as f:
            _, self._obo, _ = OboParser().parse(f)

    def find_gene_for_alignment(self, read_aln):
        '''
        given a SAMRecord aligned to the CARD database, return the ARO id,
        name and description for the reference sequence.
        '''
        *_, aro_id, _ = read_aln.rname.split('|')
        return self.describe_aro_id(aro_id)

    def describe_aro_id(self, aro_id):
        '''
        describe a aro_id
        '''
        return (self._aro[aro_id]['name'],
                aro_id,
                self._aro[aro_id]['description'])

    def is_a(self, aro_id):
        '''
        get parents for an ARO id
        '''
        return [self.describe_aro_id(x) for x in self._obo[
            aro_id].relations[Relationship('is_a')]]

    def find_antibiotics_resisted(self, aro_id):
        '''
        Get confers_resistance_to relationships for a drug ARO id.
        '''
        obo_data = self._obo[aro_id]
        try:
            resists = obo_data.relations[
                    Relationship('confers_resistance_to_drug')]
            return [self.describe_aro_id(aro_id) for aro_id in resists]
        except KeyError:
            return []


def find_mapped_reads(sam_file):
    '''
    Filter reads for mapped reads only.
    '''
    for read in sam_file:
        if not read.rname == '*':
            yield read


STARTSWITH_STOPWORDS = ['miscellaneous', 'peptide', 'antibiotic']
ENDSWITH_STOPWORDS = ['mixture', 'molecule']


def filter_parent_stopwords(antibiotics):
    filtered = []
    for a in antibiotics:
        keep = True
        for pat in STARTSWITH_STOPWORDS:
            if a.startswith(pat):
                keep = False
        for pat in ENDSWITH_STOPWORDS:
            if a.endswith(pat):
                keep = False
        if keep:
            filtered.append(a.replace(' antibiotic', ''))
    return set(filtered)


def alignment_to_card_data(sam_aln, aro):
    '''
    Takes an instance of a SAMFile and AROJSON.
    Returns a counter of CARD genes found in the alignment file, and the number
    of reads supporting them. Also the antibiotics resisted by those genes, and
    the broader groups of antibiotics these belong to.
    '''
    gene_counter = Counter()
    antib_set = set()
    antib_parent_set = set()
    for record in find_mapped_reads(sam_aln):
        gene_aro_data = aro.find_gene_for_alignment(
            record)
        gene_counter[gene_aro_data[0]] += 1
        antib_aro_data = aro.find_antibiotics_resisted(gene_aro_data[1])
        if antib_aro_data:
            antib_set.update([x[0] for x in antib_aro_data])
            for antib in antib_aro_data:
                antib_parent_data = aro.is_a(antib[1])
                if antib_parent_data:
                    antib_parent_set.update([a[0] for a in antib_parent_data])
    return gene_counter, antib_set, filter_parent_stopwords(antib_parent_set)
        