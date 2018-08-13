import threading
import requests
import base64
import queue
import json
import time

from .. import http
from .. import proxy

class worker(threading.Thread):
    def __init__(self, endpoint, period, max_queue=2048):
        super().__init__()
        self.endpoint = endpoint
        self.period = period

        self.send_queue = queue.Queue(max_queue)
        self.recv_queue = queue.Queue(max_queue)

        self.dead = False

    def close(self):
        requests.delete(self.endpoint)
        self.dead = True

    def die(self, e):
        if self.dead:
            return

        self.close()
        raise e

    def send(self, cell, block=True):
        try:
            cell = cell.raw
        except AttributeError:
            pass

        cell = base64.b64encode(cell)
        self.send_queue.put(cell, block)

    def recv(self, block=True):
        payload = self.recv_queue.get(block=block)
        payload = base64.b64decode(payload)
        return payload

    def main(self):
        try:
            cells = []
            for _ in range(proxy.jobs.request_max_cells):
                try:
                    cells.append(self.send_queue.get(block=False))
                except queue.Empty as e:
                    if len(cells) == 0:
                        raise e

            data = json.dumps(
                dict(cells=[str(cell, 'utf8') for cell in cells]))

            rq = requests.post(self.endpoint, data=data, headers=http.headers)
            if not rq.status_code == 201:
                raise RuntimeError(
                    'Got {} status (send)!'.format(rq.status_code))

            answer = json.loads(rq.text)
            for cell in answer['cells']:
                self.recv_queue.put(cell)

            return
        except queue.Empty:
            pass

        data = json.dumps(dict(cells=[]))
        rq = requests.post(self.endpoint, data=data, headers=http.headers)
        if not rq.status_code == 201:
            raise RuntimeError('Got {} status! (recv)'.format(rq.status_code))

        answer = json.loads(rq.text)
        for cell in answer['cells']:
            self.recv_queue.put(cell)

        time.sleep(self.period)

    def run(self):
        try:
            while not self.dead:
                self.main()
            self.dead = True
        except BaseException as e:
            self.die(e)

class io:
    _join_timeout = 3

    def __init__(self, endpoint, period=0.1, daemon=True, max_queue=2048):
        self.worker = worker(endpoint, period, max_queue)
        if daemon:
            self.worker.daemon = True

        self.worker.start()

    @property
    def dead(self):
        return self.worker.dead

    def recv(self, block=True):
        return self.worker.recv(block)

    def send(self, payload, block=True):
        self.worker.send(payload, block=block)

    def close(self):
        self.worker.close()
        self.worker.join(self._join_timeout)
