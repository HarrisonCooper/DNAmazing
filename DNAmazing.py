from collections import namedtuple
import json
# pronto OBO format parser
from pronto.parser import OboParser
from pronto.parser.obo import Relationship


SAMRecord = namedtuple(
    'SAMRecord',
    'qname flag rname pos mapq cigar rnext pnext tlen seq qual')


class SAMFile(object):

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


def find_mapped_reads(sam_file):
    for read in sam_file:
        if not read.rname == '*':
            yield read


class AROJSON(object):

    def __init__(self, json_fn, obo_fn):
        self._json_fn = json_fn
        self._obo_fn = obo_fn
        with open(json_fn) as f:
            self._aro = json.load(f)
            self._aro = {x.pop('accession'): x for x in self._aro}
        with open(obo_fn, 'rb') as f:
            _, self._obo, _ = OboParser().parse(f)

    def find_gene_for_alignment(self, read_aln):
        *_, aro_id, _ = read_aln.rname.split('|')
        return self.describe_aro_id(aro_id)

    def describe_aro_id(self, aro_id):
        return (self._aro[aro_id]['name'],
                aro_id,
                self._aro[aro_id]['description'])

    def find_antibiotics_resisted(self, aro_id):
        obo_data = self._obo[aro_id]
        try:
            resists = obo_data.relations[
                    Relationship('confers_resistance_to_drug')]
            return [self.describe_aro_id(aro_id) for aro_id in resists]
        except KeyError:
            return []
