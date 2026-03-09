# Docker Container → Host Communication: Use Gateway IP, Not Public IP

## Trigger

Use when:
- Container cannot reach a service running on the HOST (same server)
- UDP/TCP query to `vinicius.xyz` or public IP fails with timeout inside the container
- `127.0.0.1` inside the container points to the container itself, not the host
- Services like CS:GO, databases, or local APIs are unreachable from the container

## The Problem

Inside a Docker container, there are 3 ways to try to reach the host — and 2 of them fail:

| Host Reference | Works? | Reason |
|---|---|---|
| `127.0.0.1` | NO | Container's loopback, not the host's |
| `vinicius.xyz` / public IP | NO | NAT hairpin blocked by FORWARD DROP |
| `172.18.0.1` (network gateway) | YES | Direct route to host via bridge |

Docker creates a bridge network for each `docker network`. The **gateway of that network** is the host's IP as seen from inside the containers on that network.

## How to Find the Correct Gateway

```bash
# Check which network the container uses (look in docker-compose.yml)
docker network inspect <network-name> | grep Gateway
# Example: npm_default → 172.18.0.1
# Example: default bridge → 172.17.0.1
```

## Configuration in docker-compose.yml

```yaml
environment:
  # WRONG: CSGO_SERVER_HOST=vinicius.xyz
  # WRONG: CSGO_SERVER_HOST=127.0.0.1
  - CSGO_SERVER_HOST=172.18.0.1  # gateway of npm_default network
```

## Testing Connectivity From Inside the Container

```bash
# UDP test (e.g., gamedig for CS:GO)
docker exec <container> node -e "
const { GameDig } = require('gamedig');
['172.18.0.1','127.0.0.1','hostname.xyz'].forEach(host =>
  GameDig.query({ type: 'csgo', host, port: 27015, maxAttempts: 1, attemptTimeout: 3000 })
    .then(r => console.log('OK', host))
    .catch(e => console.log('FAIL', host, e.message))
);"

# Generic TCP/UDP test
docker exec <container> node -e "
const dgram = require('dgram');
const s = dgram.createSocket('udp4');
s.send(Buffer.from('test'), PORT, HOST, () => {});
s.on('message', m => { console.log('got reply'); s.close(); });
setTimeout(() => { console.log('no reply'); s.close(); }, 3000);"
```

## Note: Gateway Can Change

The gateway (e.g., `172.18.0.1`) is fixed as long as the Docker network exists, but it can change if the network is recreated. For production where the network is stable (e.g., `npm_default` from Nginx Proxy Manager), the IP is reliable.

More robust alternative: `extra_hosts: ["host.docker.internal:host-gateway"]` in docker-compose, then use `host.docker.internal` as hostname.
