import flatdict
import time

# Prometheus specific imports
from prometheus_client import REGISTRY, start_wsgi_server
from prometheus_client.metrics_core import (
    GaugeMetricFamily, InfoMetricFamily, CounterMetricFamily)

# Horizon API Specific imports
from .horizon_api import horizon_connection_server


class HorizonExporter:
    def __init__(self):
        self.horizon = horizon_connection_server()

    def _create_metric_list(self):

        self._label_names = {
            'gateways': ['name'],
            'connection_servers': ['name'],
        }

        self.metric_list = {}
        self.metric_list['gateways'] = {
            'active_connection_count': GaugeMetricFamily(
                'horizon_gateway_active_connection_count',
                'VMware Horizon Gateway Active Connection Count',
                labels=self._label_names['gateways']),
            'pcoip_connection_count': GaugeMetricFamily(
                'horizon_gateway_pcoip_connection_count',
                'VMware Horizon Gateway PCoIP Connection Count',
                labels=self._label_names['gateways']),
            'blast_connection_count': GaugeMetricFamily(
                'horizon_gateway_blast_connection_count',
                'VMware Horizon Gateway Blast Connection Count',
                labels=self._label_names['gateways']),
            'unrecognized_pcoip_requests_count': GaugeMetricFamily(
                'horizon_gateway_unrecognized_pcoip_requests_count',
                'VMware Horizon Gateway Unrecognized PCoIP Requests Count',
                labels=self._label_names['gateways']),
            'unrecognized_tunnel_requests_count': GaugeMetricFamily(
                'horizon_gateway_unrecognized_tunnel_requests_count',
                'VMware Horizon Gateway Unrecognized Tunnel Requests Count',
                labels=self._label_names['gateways']),
            'unrecognized_xmlapi_requests_count': GaugeMetricFamily(
                'horizon_gateway_unrecognized_xmlapi_requests_count',
                'VMware Horizon Gateway Unrecognized XML API Requests Count',
                labels=self._label_names['gateways']),
            'details': InfoMetricFamily(
                'horizon_gateway',
                'VMware Horizon Gateway Internal Details',
                labels=self._label_names['gateways'] +
                ['type', 'address', 'internal', 'version']),
            'status': InfoMetricFamily(
                'horizon_gateway_status',
                'VMware Horizon Gateway Status',
                labels=self._label_names['gateways'] + ['status']),
            'last_updated_timestamp': GaugeMetricFamily(
                'horizon_gateway_last_updated',
                'VMware Horizon Gateway last updated',
                labels=self._label_names['gateways']),
        }

        self.metric_list['connection_servers'] = {
            'connection_count': GaugeMetricFamily(
                'horizon_connection_server_connection_count',
                'VMware Horizon Connection Server Connection Count',
                labels=self._label_names['connection_servers']),
            'tunnel_connection_count': GaugeMetricFamily(
                'horizon_connection_server_tunnel_connection_count',
                'VMware Horizon Connection Server Tunnel Connection Count',
                labels=self._label_names['connection_servers']),
            'unrecognized_pcoip_requests_count': GaugeMetricFamily(
                'horizon_connection_server_unrecognized_pcoip_requests_count',
                'VMware Horizon Connection Server Unrecognized PCoIP '
                'Requests Count',
                labels=self._label_names['connection_servers']),
            'unrecognized_tunnel_requests_count': GaugeMetricFamily(
                'horizon_connection_server_unrecognized_tunnel_requests_count',
                'VMware Horizon Connection Server Unrecognized Tunnel '
                'Requests Count',
                labels=self._label_names['connection_servers']),
            'unrecognized_xmlapi_requests_count': GaugeMetricFamily(
                'horizon_connection_server_unrecognized_xmlapi_requests_count',
                'VMware Horizon Connection Server Unrecognized XML API '
                'Requests Count',
                labels=self._label_names['connection_servers']),
            'details': InfoMetricFamily(
                'horizon_connection_server',
                'VMware Horizon Connecton Server Internal Details',
                labels=self._label_names['connection_servers'] +
                ['build', 'version']),
            'status': InfoMetricFamily(
                'horizon_connection_server_status',
                'VMware Horizon Connection Server Status',
                labels=self._label_names['connection_servers'] + ['status']),
            'cs_replications': InfoMetricFamily(
                'horizon_connection_server_replication',
                'VMware Horizon Connection Server Replication Info',
                labels=self._label_names['connection_servers'] +
                ['server_name', 'status']),
            'services': InfoMetricFamily(
                'horizon_connection_server_service',
                'VMware Horizon Connection Server Service Info',
                labels=self._label_names['connection_servers'] +
                ['service_name', 'status']),
            'certificate.valid_from': GaugeMetricFamily(
                'horizon_connection_server_certificate_valid_from',
                'VMware Horizon Connection Server Certificate Valid From',
                labels=self._label_names['connection_servers']),
            'certificate.valid_to': GaugeMetricFamily(
                'horizon_connection_server_certificate_valid_to',
                'VMware Horizon Connection Server Certificate Valid To',
                labels=self._label_names['connection_servers']),
            'last_updated_timestamp': GaugeMetricFamily(
                'horizon_connection_server_last_updated',
                'VMware Horizon Connection Server last updated',
                labels=self._label_names['connection_servers']),
        }

        self.metric_list['sessions'] = {}

    def collect(self):
        self._create_metric_list()

        connection = self.horizon.get_monitor_connection_servers()

        conn = []
        for c in connection:
            d = flatdict.FlatDict({'certificate': c['certificate']},
                                  delimiter='.')
            for k, v in d.items():
                c[k] = v
            conn.append(c)

        api_data = {
            'gateways': self.horizon.get_monitor_gateways(),
            'sessions': self.horizon.get_inventory_sessions(),
            'connection_servers': conn
        }

        for list_key, all_data in api_data.items():
            for key, metric in self.metric_list[list_key].items():
                if type(metric) is GaugeMetricFamily:
                    for _data in all_data:
                        labels = [_data['name']]
                        metric.add_metric(labels, float(_data[key]))
                    yield metric
                elif type(metric) is CounterMetricFamily:
                    for _data in all_data:
                        labels = [_data['name']]
                        metric.add_metric(labels, int(_data[key]))
                    yield metric
                elif type(metric) is InfoMetricFamily:
                    for _data in all_data:
                        labels = [_data['name']]
                        if type(_data[key]) is dict:
                            _dict = [_data[key]]
                        elif type(_data[key]) is list:
                            _dict = _data[key]
                        elif type(_data[key]) is not dict:
                            _dict = [{key: _data[key]}]
                        for _d in _dict:
                            metric.add_metric(
                                labels,
                                {key: str(val) for key, val in _d.items()}
                            )
                    yield metric


def main():
    REGISTRY.register(HorizonExporter())

    start_wsgi_server(18000)
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
