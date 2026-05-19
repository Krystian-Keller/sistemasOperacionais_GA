# Simulacao de Escalonamento de Pods

Projeto em Python para uma disciplina de Sistemas Operacionais. A aplicacao simula um ambiente inspirado no Kubernetes, com um Master, Workers e Pods. O objetivo e comparar um scheduler padrao simplificado com um scheduler customizado que usa mais metricas.

Esta simulacao nao e uma reimplementacao real do `kube-scheduler`. Ela apenas representa, de forma academica e simplificada, a ideia de um Master escolhendo em quais Workers os Pods devem ser alocados conforme recursos disponiveis.

## Estrutura

```text
app/
  main.py
  models.py
  schedulers.py
  simulation.py
  statistics.py
README.md
```

## Como executar

Use Python 3.10 ou superior.

```bash
python app/main.py
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
- Nao ha Docker, Prometheus ou Grafana nesta versao.
- A simulacao usa dados fixos para facilitar a apresentacao oral.
- O algoritmo e propositalmente simples para ficar claro em uma disciplina introdutoria.
