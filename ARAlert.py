import os
import click
import nexmo
import DNAmazing as dna


@click.command()
@click.option('--aln-file', '-a', required=True, help='SAM alignment to CARD')
@click.option('--aro-file', '-j', required=True, help='Path to aro.json')
@click.option('--to-number', '-t', required=True,
              help='Number to send to')
@click.option('--from-number', '-f', required=True,
              help='Nexmo number to send from')
@click.option('--key', '-k', required=True, help='Nexmo API key')
@click.option('--secret', '-s', required=True, help='Nexmo API secret')
def ARAlert(aln_file, aro_file, to_number, from_number, key, secret):
    aro_obo = os.path.splitext(aro_file)[0] + '.obo'
    aro = dna.AROJSON(aro_file, aro_obo)
    sam = dna.SAMFile(aln_file)
    gene_names, antibiotics, antibiotic_groups = dna.alignment_to_card_data(
        sam, aro)
    sample_name = os.path.splitext(os.path.split(aln_file)[1])[0]
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
