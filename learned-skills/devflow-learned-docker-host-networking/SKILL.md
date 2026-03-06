# Docker Container → Host Communication: Use Gateway IP, Not Public IP

## Trigger

Use when:
- Container não consegue alcançar um serviço rodando no HOST (mesmo servidor)
- Query UDP/TCP para `vinicius.xyz` ou IP público falha com timeout dentro do container
- `127.0.0.1` dentro do container aponta para o próprio container, não para o host
- Serviços como CS:GO, bancos de dados, ou APIs locais ficam inacessíveis do container

## O Problema

Dentro de um container Docker, existem 3 formas de tentar alcançar o host — e 2 delas falham:

| Host Referência | Funciona? | Motivo |
|---|---|---|
| `127.0.0.1` | NÃO | Loopback do container, não do host |
| `vinicius.xyz` / IP público | NÃO | NAT hairpin bloqueado pelo FORWARD DROP |
| `172.18.0.1` (gateway da rede) | SIM | Rota direta para o host via bridge |

O Docker cria uma rede bridge para cada `docker network`. O **gateway dessa rede** é o IP do host como visto de dentro dos containers naquela rede.

## Como Descobrir o Gateway Correto

```bash
# Ver qual rede o container usa (olhar no docker-compose.yml)
docker network inspect <nome-da-rede> | grep Gateway
# Exemplo: npm_default → 172.18.0.1
# Exemplo: bridge padrão → 172.17.0.1
```

## Configuração no docker-compose.yml

```yaml
environment:
  # ERRADO: CSGO_SERVER_HOST=vinicius.xyz
  # ERRADO: CSGO_SERVER_HOST=127.0.0.1
  - CSGO_SERVER_HOST=172.18.0.1  # gateway da rede npm_default
```

## Testar Conectividade de Dentro do Container

```bash
# Teste UDP (ex: gamedig para CS:GO)
docker exec <container> node -e "
const { GameDig } = require('gamedig');
['172.18.0.1','127.0.0.1','hostname.xyz'].forEach(host =>
  GameDig.query({ type: 'csgo', host, port: 27015, maxAttempts: 1, attemptTimeout: 3000 })
    .then(r => console.log('OK', host))
    .catch(e => console.log('FAIL', host, e.message))
);"

# Teste TCP/UDP genérico
docker exec <container> node -e "
const dgram = require('dgram');
const s = dgram.createSocket('udp4');
s.send(Buffer.from('test'), PORT, HOST, () => {});
s.on('message', m => { console.log('got reply'); s.close(); });
setTimeout(() => { console.log('no reply'); s.close(); }, 3000);"
```

## Nota: Gateway pode mudar

O gateway (ex: `172.18.0.1`) é fixo enquanto a rede Docker existir, mas pode mudar se a rede for recriada. Para produção onde a rede é estável (ex: `npm_default` do Nginx Proxy Manager), o IP é confiável.

Alternativa mais robusta: `extra_hosts: ["host.docker.internal:host-gateway"]` no docker-compose, então usar `host.docker.internal` como hostname.
