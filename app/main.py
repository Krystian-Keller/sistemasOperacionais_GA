import argparse

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
    args = parser.parse_args()

    run_comparison(verbose=args.verbose)
