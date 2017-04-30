import os
import click
import pandas as pd
import nexmo
import DNAmazing as dna


@click.command()
@click.option('--fastq', '-i', required=True, help='ONT reads to map')
@click.option('--aro-dir', '-j', required=True,
              help='Path to directory containing aro.json, etc')
@click.option('--output', '-o', required=True,
              help='Path to output csv')
@click.option('--to-number', '-t', required=True,
              help='Number to send to')
@click.option('--from-number', '-f', required=True,
              help='Nexmo number to send from')
@click.option('--key', '-k', required=True, help='Nexmo API key')
@click.option('--secret', '-s', required=True, help='Nexmo API secret')
@click.option('--email-from', '-e', required=True,
              help='email address to send from')
@click.option('--email-password', '-p', required=True,
              help='email address password')
@click.option('--email-to', '-r', required=True,
              help='email address to send to')
def ARAlert(fastq, aro_dir, output,
            to_number, from_number, key, secret,
            email_from, email_password, email_to):
    card_seqs_fn, aro_json_fn, aro_obo_fn = dna.check_card(aro_dir)
    aro = dna.AROJSON(aro_json_fn, aro_obo_fn)
    sam = dna.SAMFile(dna.run_bwa(fastq, card_seqs_fn))
    all_antibiotic_data, antibiotic_groups = dna.alignment_to_card_data(
        sam, aro)
    all_antibiotic_data.to_csv(output, sep=',', index=False)
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
    dna.send_email(antibiotic_groups, sample_name, output,
                   email_from, email_to, email_password)

if __name__ == '__main__':
    ARAlert()
