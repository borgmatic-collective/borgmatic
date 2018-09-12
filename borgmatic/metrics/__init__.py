import logging


def create_metrics(metrics: dict):
    borg_output_logger = logging.getLogger('borg_output')
    borg_output = borg_output_logger.handlers[0].stream.getvalue()

    if 'prometheus' in metrics.keys():
        from .prometheus import PrometheusOutput
        prom_out = PrometheusOutput(borg_output)
        prom_out.write_file(path=metrics['prometheus']['path'])
