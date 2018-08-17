import random
import base64
import io

import nacl.public

import lighttor as ltor

def circuit(state, descriptor):
    onion_key = base64.b64decode(descriptor['ntor-onion-key'] + '====')
    eidentity = descriptor['identity']['master-key'] # (assuming ed25519 here)
    identity = base64.b64decode(descriptor['router']['identity'] + '====')
    addr = descriptor['router']['address']
    port = descriptor['router']['orport']

    eph_key, hdata = ltor.crypto.ntor.hand(identity, onion_key)

    payload = ltor.cell.relay.extend2.pack(
        hdata, [(addr, port)], [identity, eidentity])

    state = ltor.hop.send(state,
        ltor.cell.relay.cmd.RELAY_EXTEND2, payload.raw, stream_id=0)

    state, cells = ltor.hop.recv(state, once=True)
    if not len(cells) == 1:
        raise RuntimeError('Expected exactly one cell, got: {}'.format(cells))

    if not cells[0].relay.cmd == ltor.cell.relay.cmd.RELAY_EXTENDED2:
        raise RuntimeError('Expected EXTENDED2, got {} here: {}'.format(
            cells[0].relay.cmd, cell.relay.truncated))

    payload = ltor.cell.relay.extended2.payload(cells[0].relay.data)
    if not payload.valid:
        raise RuntimeError('Invalid EXTENDED2 payload: {}'.format(
            payload.truncated))

    raw_material = ltor.crypto.ntor.shake(eph_key, payload.data, identity,
        onion_key, length=92)

    material = ltor.crypto.ntor.kdf(raw_material)
    extended = ltor.create.circuit(state.circuit.id, material)

    state.wrap(ltor.onion.state(state.link, extended))
    return state
