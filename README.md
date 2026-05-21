# Simulacao de Escalonamento de Pods

Projeto em Python para uma disciplina de Sistemas Operacionais. A aplicacao simula um ambiente inspirado no Kubernetes, com um Master, Workers e Pods. O objetivo e comparar um scheduler padrao simplificado com um scheduler customizado que usa mais metricas.

Esta simulacao nao e uma reimplementacao real do `kube-scheduler`. Ela apenas representa, de forma academica e simplificada, a ideia de um Master escolhendo em quais Workers os Pods devem ser alocados conforme recursos disponiveis.

## Estrutura

```text
app/
  main.py
  metrics.py
  models.py
  schedulers.py
  simulation.py
  statistics.py
grafana/
  dashboards/
  provisioning/
Dockerfile
docker-compose.yml
prometheus.yml
requirements.txt
README.md
```

## Como executar

Use Python 3.10 ou superior.

Execucao padrao, com resumo final e tabela comparativa:

```bash
python app/main.py
```

Execucao verbose, mostrando produtor, buffer e consumidor:

```bash
python app/main.py --verbose
```

Execucao local com endpoint Prometheus em `/metrics`:

```bash
pip install -r requirements.txt
python app/main.py --serve-metrics
```

Execucao local com metricas em modo continuo:

```bash
python app/main.py --serve-metrics --continuous
```

Depois acesse:

```text
http://localhost:8000/metrics
```

## Como executar com Docker Compose

```bash
docker compose up --build
```

Por padrao, o Compose usa o modo estatico, que roda a simulacao uma vez e mantem as metricas finais expostas. Para ativar o modo continuo no Compose:

```bash
SIMULATION_CONTINUOUS=true docker compose up --build
```

Tambem e possivel ajustar:

```bash
SIMULATION_CONTINUOUS=true SIMULATION_CYCLE_SECONDS=3 SIMULATION_PODS_PER_CYCLE=5 docker compose up --build
```

Servicos disponiveis:

- Aplicacao Python: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

Login padrao do Grafana:

```text
usuario: admin
senha: admin
```

## O que a simulacao faz

- Cria um Master.
- Cria 3 Workers simulados.
- Cria 18 Pods com demandas diferentes.
- Executa um scheduler padrao simplificado que considera apenas CPU e memoria.
- Executa um scheduler customizado que considera CPU, memoria, disco e latencia.
- Usa uma thread produtora para criar/enfileirar Pods.
- Usa uma thread consumidora representando o Master/Scheduler.
- Usa um buffer compartilhado limitado, sem `queue.Queue`.
- Usa `threading.Semaphore` para controlar espacos vazios e itens disponiveis.
- Usa `threading.Lock` como mutex para proteger o acesso ao buffer.
- Mostra a alocacao final dos Pods por Worker.
- Mostra recursos usados e disponiveis em cada Worker.
- Mostra overcommit de disco quando o scheduler padrao aloca alem da capacidade.
- Mostra estatisticas finais da simulacao.
- Mostra gargalos por Worker acima de 90% de CPU, memoria ou disco.
- Mostra Pods alocados validos, Pods com violacao, violacoes de latencia e motivos de rejeicao.
- Compara os dois schedulers usando os mesmos Pods e Workers.
- Gera uma tabela final lado a lado para facilitar a apresentacao.
- Exporta metricas Prometheus com labels por scheduler e Worker.

## Observabilidade

A arquitetura de observabilidade possui tres servicos no `docker-compose.yml`:

- `scheduler-simulator`: executa a simulacao Python e expoe `/metrics` na porta 8000.
- `prometheus`: coleta as metricas da aplicacao a cada 5 segundos.
- `grafana`: usa o Prometheus como datasource e carrega um dashboard inicial.

Existem dois modos de metricas:

- Modo estatico: melhor para comparacao academica, pois executa a mesma simulacao fixa uma vez e compara claramente o scheduler `default` com o `custom`.
- Modo continuo: melhor para demonstracao visual no Grafana, pois executa ciclos periodicos, gera novos Pods, expira Pods antigos, libera recursos dos Workers e atualiza as metricas ao longo do tempo.

No modo continuo, cada Pod recebe uma duracao em ciclos (`duration_cycles`). A cada ciclo, a duracao dos Pods em execucao diminui. Quando chega a zero, o Pod e removido do Worker e seus recursos de CPU, memoria e disco sao liberados.

As metricas principais exportadas sao:

- `pods_total`
- `pods_allocated_total`
- `pods_valid_allocated_total`
- `pods_with_violation_total`
- `pods_pending_total`
- `worker_cpu_used`
- `worker_cpu_available`
- `worker_memory_used`
- `worker_memory_available`
- `worker_disk_used`
- `worker_disk_available`
- `worker_pods_allocated`
- `worker_disk_overcommit`
- `latency_violations_total`
- `simulation_cycle`

As metricas de scheduler usam a label `scheduler`, com valores como `default` e `custom`. As metricas por Worker tambem usam a label `worker`, por exemplo `worker="worker-a-fast"`.

Para verificar se o endpoint esta funcionando:

```bash
curl http://localhost:8000/metrics
```

Procure por linhas como:

```text
pods_allocated_total{scheduler="default"} 14.0
pods_allocated_total{scheduler="custom"} 13.0
worker_disk_overcommit{scheduler="default",worker="worker-c-balanced"} 136.0
```

Para verificar se o Prometheus esta coletando:

1. Acesse `http://localhost:9090`.
2. Abra `Status > Targets`.
3. Confirme que o target `scheduler-simulator:8000` esta como `UP`.
4. Pesquise uma metrica, por exemplo `pods_allocated_total`.

Para acessar o dashboard no Grafana:

1. Acesse `http://localhost:3000`.
2. Entre com `admin` / `admin`.
3. Abra `Dashboards`.
4. Entre na pasta `Scheduler Simulator`.
5. Abra o dashboard `Scheduler Simulator`.

O dashboard inicial possui paineis simples para Pods alocados, Pods validos, Pods com violacao, Pods pendentes, uso de CPU, memoria e disco por Worker, overcommit de disco e violacoes de latencia.
No modo continuo, esses paineis passam a apresentar variacao temporal real.

## Produtor/Consumidor

Cada execucao de scheduler usa uma thread produtora e uma thread consumidora:

- a produtora cria os Pods na mesma ordem fixa e os insere em um buffer limitado;
- a consumidora representa o Master/Scheduler e retira Pods do buffer para escalonar;
- o buffer tem capacidade maxima de 5 Pods;
- um semaforo controla espacos livres no buffer;
- outro semaforo controla itens disponiveis para consumo;
- um mutex protege a lista compartilhada usada como buffer;
- ao final, a produtora insere um sentinel `None` para encerrar a consumidora.

Essa parte demonstra o paradigma produtor/consumidor sem alterar a ideia central dos algoritmos de escalonamento.

Por padrao, esses logs ficam ocultos para deixar a comparacao final mais limpa. Use `--verbose` para mostrar passo a passo os Pods sendo produzidos, inseridos no buffer, consumidos pelo Master/Scheduler e alocados ou rejeitados.

## Schedulers

### Scheduler padrao simplificado

Considera apenas se o Worker possui CPU e memoria suficientes para receber o Pod. Entre os Workers possiveis, escolhe aquele que fica com melhor pontuacao media de CPU e memoria livres apos a alocacao.

### Scheduler customizado

Considera CPU, memoria, disco e latencia. Um Worker so pode receber um Pod se:

- tiver CPU suficiente;
- tiver memoria suficiente;
- tiver disco suficiente;
- tiver latencia de rede menor ou igual ao requisito de latencia do Pod.

A pontuacao usada e simples e explicavel:

```text
score = 0.25 * cpu_score
      + 0.25 * memory_score
      + 0.35 * disk_score
      + 0.15 * latency_score
```

Onde:

- `cpu_score` representa a proporcao de CPU que sobraria no Worker;
- `memory_score` representa a proporcao de memoria que sobraria no Worker;
- `disk_score` representa a proporcao de disco que sobraria no Worker;
- `latency_score` favorece Workers com menor latencia em relacao ao requisito do Pod.

O disco recebe peso maior para deixar a comparacao mais didatica. Tambem existe uma pequena penalidade quando a alocacao deixaria o Worker com mais de 90% de disco usado. Isso evita concentrar disco em um unico Worker quando ha alternativa melhor.

## Limitacoes

- Nao existe comunicacao real com Kubernetes.
- Nao ha containers reais.
- A simulacao usa dados fixos para facilitar a apresentacao oral.
- O algoritmo e propositalmente simples para ficar claro em uma disciplina introdutoria.
- No modo estatico, as metricas representam os valores finais de uma unica execucao.
- Para visualizar variacao temporal, use `--continuous` ou `SIMULATION_CONTINUOUS=true`.
- Se a simulacao for alterada, os paineis do Grafana podem precisar de pequenos ajustes nas consultas.
