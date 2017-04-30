import os
import click
import nexmo
import DNAmazing as dna


@click.command()
@click.option('--fastq', '-f', required=True, help='ONT reads to map')
@click.option('--aro-dir', '-j', required=True,
              help='Path to directory containing aro.json, etc')
@click.option('--to-number', '-t', required=True,
              help='Number to send to')
@click.option('--from-number', '-f', required=True,
              help='Nexmo number to send from')
@click.option('--key', '-k', required=True, help='Nexmo API key')
@click.option('--secret', '-s', required=True, help='Nexmo API secret')
def ARAlert(fastq, aro_dir, to_number, from_number, key, secret):
    card_seqs_fn, aro_json_fn, aro_obo_fn = dna.check_card(aro_dir)
    aro = dna.AROJSON(aro_json_fn, aro_obo_fn)
    sam = dna.SAMFile(dna.run_bwa(fastq, card_seqs_fn))
    gene_names, antibiotics, antibiotic_groups = dna.alignment_to_card_data(
        sam, aro)
    sample_name = os.path.splitext(os.path.split(fastq)[1])[0]
    if antibiotic_groups:
        message = ('Possible AR genes found in sample {}. '
                   'Strain may resist:\n {}.').format(
                       sample_name, ',\n'.join(antibiotic_groups))
    else:
        message = 'No AR genes found in sample {}.'.format(sample_name)
    client = nexmo.Client(key=key, secret=secret)
    response = client.send_message({'from': from_number,
                                    'to': to_number,
                                    'text': message})
    if response['messages'][0]['status'] == '0':
        print('Message sent')
    else:
        print('Message send failed')

if __name__ == '__main__':
    ARAlert()
