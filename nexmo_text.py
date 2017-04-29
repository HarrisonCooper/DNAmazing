import click
import nexmo


@click.command()
@click.option('--message', '-m', required=True, help='Message to send')
@click.option('--to-number', '-t', required=True,
              help='Number to send to')
@click.option('--from-number', '-f', required=True,
              help='Nexmo number to send from')
@click.option('--key', '-k', required=True, help='Nexmo API key')
@click.option('--secret', '-s', required=True, help='Nexmo API secret')
def send_message(message, to_number, from_number, key, secret):
    client = nexmo.Client(key=key, secret=secret)
    response = client.send_message({'from': from_number,
                                    'to': to_number,
                                    'text': message})
    if response['messages'][0]['status'] == '0':
        print('Message sent')
    else:
        print('Message send failed')

if __name__ == '__main__':
    send_message()
