lighttor.stream = {}
lighttor.stream.backend = function(error)
{
    var sendme = function(endpoint, cell)
    {
        if (cell.cmd == "sendme")
            endpoint.stream.sendme += 1
        else
        {
            console.log("Got unexpected control cell: ", cell.cmd)
            error(endpoint)
        }
    }

    var backend = {
        id: 0,
        sendme: 0,
        handles: {0: {callback: sendme}},
        register: function(handle)
        {
            backend.id += 1
            handle.id = backend.id
            backend.handles[backend.id] = handle
            return backend.id
        }
    }
    return backend
}

lighttor.stream.handler = function(endpoint)
{
    var cell = endpoint.io.recv()
    for (; cell !== undefined; cell = endpoint.io.recv())
    {
        if (cell[4] != 3) // (relay cell only)
        {
            console.log("Got non-relay cell, dropped: ", cell[4])
            continue
        }

        cell = lighttor.onion.peel(endpoint, cell)
        if (cell == null)
        {
            console.log("Got invalid cell, dropped.")
            continue
        }

        if (!(cell.stream_id in endpoint.stream.handles))
        {
            console.log("Got cell outside stream, dropped: ", cell.stream_id)
            continue
        }

        var handle = endpoint.stream.handles[cell.stream_id]
        if (cell.cmd == "end")
            delete endpoint.stream.handles[cell.stream_id]
        handle.callback(cell)
    }
}

lighttor.stream.raw = function(endpoint, handler)
{
    var request = {
        id: null,
        data: [],
        send: function(cmd, data)
        {
            var cell = lighttor.onion.build(
                request.endpoint, cmd, request.id, data)
            endpoint.io.send(cell)
        },
        recv: function()
        {
            var data = request.data
            request.data = []
            return data
        },
        state: lighttor.state.started,
        endpoint: endpoint,
        callback: function(cell)
        {
            if (cell.cmd == "connected")
            {
                request.state = lighttor.state.created
                handler(request)
                request.state = lighttor.state.pending
            }
            if (cell.cmd == "end")
            {
                request.state = lighttor.state.success
                handler(request)
            }
            request.data.push(cell)
            handler(request)
        }
    }

    var id = endpoint.stream.register(request)
    handler(request)
    return request
}

lighttor.stream.dir = function(endpoint, path, handler)
{
    var request = {
        id: null,
        data: "",
        send: function() { throw "No send method on directory streams." },
        recv: function()
        {
            var data = request.data
            request.data = ""
            return data
        },
        state: lighttor.state.started,
        endpoint: endpoint,
        callback: function(cell)
        {
            if (cell.cmd == "connected")
            {
                request.state = lighttor.state.created
                handler(request)
                request.state = lighttor.state.pending
            }
            if (cell.cmd == "end")
            {
                request.state = lighttor.state.success
                handler(request)
            }
            if (cell.cmd != "data")
                return

            request.data += lighttor.enc.utf8(cell.data)
            handler(request)
        }
    }

    var id = endpoint.stream.register(request)
    var cell = lighttor.onion.build(endpoint, "begin_dir", id)
    endpoint.io.send(cell)

    var data = "GET " + path + " HTTP/1.0\r\n"
    data += "Accept-Encoding: identity\r\n\r\n"
    data = lighttor.dec.utf8(data)

    cell = lighttor.onion.build(endpoint, "data", id, data)
    endpoint.io.send(cell)

    handler(request)
    return request
}