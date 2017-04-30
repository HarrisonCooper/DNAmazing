import os
import itertools as it
from collections import namedtuple, Counter
import json
import subprocess
import signal
import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
import pandas as pd
# pronto OBO format parser
from pronto.parser import OboParser
from pronto.parser.obo import Relationship


def run_bwa(ont_fastq, reference):
    if not os.path.exists(reference + '.bwt'):
        subprocess.call(['bwa', 'index', reference])

    def default_sigpipe():
        '''fixes some broken pipe behaviour'''
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    s = subprocess.Popen(['bwa', 'mem', '-x', 'ont2d', reference, ont_fastq],
                         stdout=subprocess.PIPE, preexec_fn=default_sigpipe)

    for record in s.stdout:
        yield record.decode().strip()
    s.stdout.close()


def check_card(path_to_card):
    required = ['nucleotide_fasta_protein_homolog_model.fasta',
                'aro.json',
                'aro.obo']
    paths_to_required = []
    for r in required:
        p = os.path.join(path_to_card, r)
        if not os.path.exists(p):
            raise IOError('Could not find {} in ARO directory {}'.format(
                r, path_to_card))
        else:
            paths_to_required.append(p)
    return paths_to_required


SAMRecord = namedtuple(
    'SAMRecord',
    'qname flag rname pos mapq cigar rnext pnext tlen seq qual')


class SAMFile(object):
    '''
    Wrapper for SAM iterator (just a tab delimited file really)
    '''
    def __init__(self, sam_iter):
        self._iter = sam_iter

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            record = next(self._iter)
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


def fix_length(lst, length):
    return (lst + ['NA'] * length)[:length]


def alignment_to_card_data(sam_aln, aro):
    '''
    Takes an instance of a SAMFile and AROJSON.
    Returns a counter of CARD genes found in the alignment file, and the number
    of reads supporting them. Also the antibiotics resisted by those genes, and
    the broader groups of antibiotics these belong to.
    '''
    gene_counter = Counter()
    gene_descriptions = set()
    antibio_parent_set = set()
    all_data = []
    for record in find_mapped_reads(sam_aln):
        g_name, aro_id, g_description = aro.find_gene_for_alignment(
            record)
        gene_counter[g_name] += 1
        gene_descriptions.add((g_name, aro_id, g_description))
    for g_name, aro_id, g_description in gene_descriptions:
        read_count = gene_counter[g_name]
        antibio_res = aro.find_antibiotics_resisted(aro_id)
        if antibio_res:
            a_names = [a[0] for a in antibio_res]
            a_desc = [a[2] for a in antibio_res]
            for antibio in antibio_res:
                antibio_parent = aro.is_a(antibio[1])
                if antibio_parent:
                    ap_names = [a[0] for a in antibio_parent]
                    antibio_parent_set.update(ap_names)
        else:
            a_names = []
            a_desc = []
        all_data.append((g_name, g_description, read_count,
                         a_names, a_desc))
    max_a = max(len(d[3]) for d in all_data)
    expanded_data = []
    for *gene, a_names, a_desc in all_data:
        a_data = it.chain(*zip(fix_length(a_names, max_a),
                               fix_length(a_desc, max_a)))
        expanded_data.append([*gene, *a_data])
    ab_r_cols = ['Antibiotic Resisted {}'.format(i + 1) for i in range(max_a)]
    ab_rd_cols = ['Antibiotic Resisted Description {}'.format(i + 1)
                  for i in range(max_a)]
    ab_cols = it.chain(*zip(ab_r_cols, ab_rd_cols))
    colnames = ['Gene Name',
                'Gene Description',
                'Reads Supporting Gene',
                *ab_cols]
    return (pd.DataFrame(expanded_data, columns=colnames),
            filter_parent_stopwords(antibio_parent_set))


MESSAGE_BASE = '''
Results from sample {sample_id}:
Strain may resist {n} antibiotic groups, including:
{antibiotics}

Full Results are attached.
'''


NO_HITS_MESSAGE = '''
No hits to AR genes found in {sample_id}
'''


def send_email(AB_resisted, sample_id, attach, email_from, email_to, password):
    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = 'Results from {}'.format(sample_id)
    if AB_resisted:
        message = MESSAGE_BASE.format(sample_id=sample_id, n=len(AB_resisted),
                                      antibiotics=',\n'.join(AB_resisted))
    else:
        message = NO_HITS_MESSAGE.format(sample_id=sample_id)
    message_body = MIMEText(message, 'plain')
    msg.attach(message_body)
    if attach is not None:
        ctype, encoding = mimetypes.guess_type(attach)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(attach, "rb") as f:
            attachment = MIMEBase(maintype, subtype)
            attachment.set_payload(f.read())
        encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition",
                              "attachment",
                              filename=attach)
        msg.attach(attachment)
        
    server = smtplib.SMTP("smtp.gmail.com:587")
    server.starttls()
    server.login(email_from, password)
    server.sendmail(email_from, email_to, msg.as_string())
    server.quit()