import argparse
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
        default=8000,
        help="porta do endpoint /metrics",
    )
    args = parser.parse_args()

    if args.serve_metrics:
        from metrics import export_metrics, start_metrics_server

        start_metrics_server(args.metrics_port)
        results = run_comparison(verbose=args.verbose)
        export_metrics(results)
        print(f"Endpoint /metrics ativo em http://0.0.0.0:{args.metrics_port}/metrics")

        while True:
            time.sleep(60)
    else:
        run_comparison(verbose=args.verbose)
