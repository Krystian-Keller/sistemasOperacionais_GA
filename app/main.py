import argparse
import os
import time

from simulation import run_comparison


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Simulacao academica de escalonamento de Pods."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="mostra logs do produtor, buffer e consumidor",
    )
    parser.add_argument(
        "--serve-metrics",
        action="store_true",
        help="mantem um servidor HTTP /metrics ativo para Prometheus",
    )
    parser.add_argument(
        "--metrics-port",
        type=int,
        default=int(os.getenv("METRICS_PORT", "8000")),
        help="porta do endpoint /metrics",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        default=os.getenv("SIMULATION_CONTINUOUS", "false").lower() == "true",
        help="executa ciclos continuos para gerar variacao temporal nas metricas",
    )
    parser.add_argument(
        "--cycle-seconds",
        type=int,
        default=int(os.getenv("SIMULATION_CYCLE_SECONDS", "5")),
        help="intervalo entre ciclos no modo continuo",
    )
    parser.add_argument(
        "--pods-per-cycle",
        type=int,
        default=int(os.getenv("SIMULATION_PODS_PER_CYCLE", "4")),
        help="quantidade de Pods gerados por ciclo no modo continuo",
    )
    args = parser.parse_args()

    if args.serve_metrics:
        from metrics import export_metrics, start_metrics_server

        start_metrics_server(args.metrics_port)
        print(f"Endpoint /metrics ativo em http://0.0.0.0:{args.metrics_port}/metrics")

        if args.continuous:
            from continuous import run_continuous_simulation

            run_continuous_simulation(
                cycle_seconds=args.cycle_seconds,
                pods_per_cycle=args.pods_per_cycle,
                verbose=args.verbose,
            )
        else:
            results = run_comparison(verbose=args.verbose)
            export_metrics(results)

            while True:
                time.sleep(60)
    else:
        if args.continuous:
            print("Aviso: --continuous so tem efeito junto com --serve-metrics.\n")
        run_comparison(verbose=args.verbose)
