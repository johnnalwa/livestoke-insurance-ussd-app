// webrtc.js

document.addEventListener('DOMContentLoaded', function () {
    var roomName = 'your_room_name';  // Set your desired room name
    var socket = io.connect('http://' + document.domain + ':' + location.port);

    var peer = new SimplePeer({ initiator: location.hash === '#1', trickle: false });

    peer.on('signal', function (data) {
        socket.emit('send_signal', { signal: data, room: roomName });
    });

    socket.on('receive_signal', function (data) {
        peer.signal(data.signal);
    });

    peer.on('connect', function () {
        console.log('CONNECT');
        peer.send('Hello from the other side!');
    });

    peer.on('data', function (data) {
        console.log('data: ' + data);
    });
});
