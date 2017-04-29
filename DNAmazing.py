from collections import namedtuple
import json


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


class CARDJSON(object):

    def __init__(self, fn):
        self._fn = fn
        with open(fn) as f:
            self._card = json.load(f)
            self._card = {
                    k: v for k, v in self._card.items()
                    if isinstance(v, dict) and 'ARO_id' in v.keys()}
        self._card_aro_idx = {
            self._card[x]['ARO_accession']: self._card[x] for x in self._card}

    def find_gene_for_alignment(self, read_aln):
        *_, aro_id, gname = read_aln.rname.split('|')
        _, aro_id = aro_id.split(':')
        return gname, self._card_aro_idx[aro_id]
