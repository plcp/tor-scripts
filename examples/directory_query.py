import lighttor as ltor

import argparse
import time

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('addr', nargs='?', default='127.0.0.1')
    parser.add_argument('port', nargs='?', type=int, default=9050)
    sys_argv = parser.parse_args()

    link = ltor.link.initiate(address=sys_argv.addr, port=sys_argv.port)
    print('Link v{} established – {}'.format(link.version, link.io))

    endpoint = ltor.create.fast(link)
    print('Circuit {} created – Key hash: {}'.format(endpoint.circuit.id,
        endpoint.circuit.material.key_hash.hex()))

    print('(sending a RELAY_DROP for fun)')
    endpoint = ltor.hop.send(endpoint, ltor.cell.relay.cmd.RELAY_DROP)

    print('\nDownloading full consensus without compression...')
    start_time = time.time()

    # Download the full consensus without compression
    endpoint, full_answer = ltor.hop.directory_query(endpoint,
        '/tor/status-vote/current/consensus', compression='identity')

    total_time = time.time() - start_time
    print('Note: consensus written to /tmp/consensus')
    with open('/tmp/consensus', 'wb') as f:
        f.write(full_answer)
    print('Took {:.2f}s to download {}o!'.format(total_time, len(full_answer)))

    print('\nDownloading full consensus without compression...')
    start_time = time.time()

    # Download the microdesc consensus with compression
    endpoint, full_answer = ltor.hop.directory_query(endpoint,
        '/tor/status-vote/current/consensus-microdesc')

    total_time = time.time() - start_time
    print('Note: microdesc consensus written to /tmp/consensus-microdesc')
    with open('/tmp/consensus-microdesc', 'wb') as f:
        f.write(full_answer)

    print('Took {:.2f}s to download {}o!'.format(total_time, len(full_answer)))
