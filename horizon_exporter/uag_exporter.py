from http.server import HTTPServer
import urllib.parse

# Prometheus specific imports
from prometheus_client import REGISTRY, MetricsHandler
from prometheus_client.metrics_core import (
    GaugeMetricFamily, InfoMetricFamily, CounterMetricFamily)

# Horizon API Specific imports
from .horizon_api import horizon_uag

# Utils
from .utils import get_nested_item


UAG = horizon_uag()


class UAGExporter:
    def _create_metric_list(self):

        self._label_names = []

        self.metric_list = [{
            'path': ['overAllStatus'],
            'metric': InfoMetricFamily(
                'horizon_uag_status',
                'VMware UAG Overall Status',
                labels=self._label_names + ['status']),
        }, {
            'path': ['uagVersion'],
            'label': 'version',
            'metric': InfoMetricFamily(
                'horizon_uag_version',
                'VMware UAG Version',
                labels=self._label_names + ['version']),
        }, {
            'path': ['sessionCount'],
            'metric': GaugeMetricFamily(
                'horizon_uag_session_count',
                'VMware UAG Session Count',
                labels=self._label_names)
        }, {
            'path': ['authenticatedSessionCount'],
            'metric': GaugeMetricFamily(
                'horizon_uag_authenicated_session_count',
                'VMware UAG Authenticated Session Count',
                labels=self._label_names)
        }, {
            'path': ['authenticatedViewSessionCount'],
            'metric': GaugeMetricFamily(
                'horizon_uag_authenicated_view_session_count',
                'VMware UAG Authenticated View Session Count',
                labels=self._label_names)
        }, {
            'path': ['openIncomingConnectionCount'],
            'metric': GaugeMetricFamily(
                'horizon_uag_open_incoming_connection_count',
                'VMware UAG Open Incoming Connection Count',
                labels=self._label_names)
        }, {
            'path': ['highWaterMark'],
            'metric': GaugeMetricFamily(
                'horizon_uag_connection_high_water_mark',
                'VMware UAG Connection High Water Mark',
                labels=self._label_names)
        }, {
            'path': ['viewEdgeServiceStats', 'backendStatus'],
            'metric': InfoMetricFamily(
                'horizon_uag_backend_status',
                'VMware UAG Backend Status',
                labels=self._label_names + ['reason', 'status']),
        }, {
            'path': ['viewEdgeServiceStats', 'edgeServiceStatus'],
            'metric': InfoMetricFamily(
                'horizon_uag_edge_service_status',
                'VMware UAG Edge Service Status',
                labels=self._label_names + ['status']),
        }, {
            'path': ['viewEdgeServiceStats', 'edgeServiceSessionStats',
                     'totalSessions'],
            'label': ['viewEdgeServiceStats', 'edgeServiceSessionStats',
                      'identifier'],
            'metric': GaugeMetricFamily(
                'horizon_uag_edge_service_total_sessions',
                'VMware UAG Edge Service Total Sessions',
                labels=self._label_names + ['identifier'])
        }, {
            'path': ['viewEdgeServiceStats', 'edgeServiceSessionStats',
                     'authenticatedSessions'],
            'label': ['viewEdgeServiceStats', 'edgeServiceSessionStats',
                      'identifier'],
            'metric': GaugeMetricFamily(
                'horizon_uag_edge_service_authenticated_sessions',
                'VMware UAG Edge Service Authenticated Sessions',
                labels=self._label_names + ['identifier'])
        }, {
            'path': ['viewEdgeServiceStats', 'edgeServiceSessionStats',
                     'unauthenticatedSessions'],
            'label': ['viewEdgeServiceStats', 'edgeServiceSessionStats',
                      'identifier'],
            'metric': GaugeMetricFamily(
                'horizon_uag_edge_service_unauthenticated_sessions',
                'VMware UAG Edge Service Unauthenticated Sessions',
                labels=self._label_names + ['identifier'])
        }, {
            'path': ['viewEdgeServiceStats', 'edgeServiceSessionStats',
                     'failedLoginAttempts'],
            'label': ['viewEdgeServiceStats', 'edgeServiceSessionStats',
                      'identifier'],
            'metric': GaugeMetricFamily(
                'horizon_uag_edge_service_failed_login_attempts',
                'VMware UAG Edge Service Failed Login Attempts',
                labels=self._label_names + ['identifier'])
        }, {
            'path': ['viewEdgeServiceStats', 'edgeServiceSessionStats',
                     'userCount'],
            'label': ['viewEdgeServiceStats', 'edgeServiceSessionStats',
                      'identifier'],
            'metric': GaugeMetricFamily(
                'horizon_uag_edge_service_user_count',
                'VMware UAG Edge Service User Count',
                labels=self._label_names + ['identifier'])
        }, {
            'path': ['viewEdgeServiceStats', 'protocol'],
            'rlabel': ['@name'],
            'rdata': 'status',
            'metric': InfoMetricFamily(
                'horizon_uag_protocol_status',
                'VMware UAG Protocol Status',
                labels=self._label_names + ['name', 'reason', 'status'])
        }, {
            'path': ['viewEdgeServiceStats', 'protocol'],
            'rlabel': ['@name'],
            'rdata': 'sessions',
            'metric': GaugeMetricFamily(
                'horizon_uag_protocol_sessions',
                'VMware UAG Protocol Sessions',
                labels=self._label_names + ['name'])
        }, {
            'path': ['viewEdgeServiceStats', 'protocol'],
            'rlabel': ['@name'],
            'rdata': 'maxSessions',
            'metric': GaugeMetricFamily(
                'horizon_uag_protocol_max_sessions',
                'VMware UAG Protocol Max Sessions',
                labels=self._label_names + ['name'])
        }, {
            'path': ['viewEdgeServiceStats', 'protocol'],
            'rlabel': ['@name'],
            'rdata': 'unrecognizedRequestsCount',
            'metric': GaugeMetricFamily(
                'horizon_uag_protocol_unrecognized_requests_count',
                'VMware UAG Protocol Unrecognized Requests Count',
                labels=self._label_names + ['name'])
        }, {
            'path': ['applianceStats', 'freeMemoryMb'],
            'metric': GaugeMetricFamily(
                'horizon_uag_appliance_mem_free',
                'VMware UAG Appliance Free Memory in Mb',
                labels=self._label_names)
        }, {
            'path': ['applianceStats', 'totalMemoryMb'],
            'metric': GaugeMetricFamily(
                'horizon_uag_appliance_mem_total',
                'VMware UAG Appliance Total Memory in Mb',
                labels=self._label_names)
        }, {
            'path': ['applianceStats', 'totalCpuLoadPercent'],
            'metric': GaugeMetricFamily(
                'horizon_uag_appliance_cpu_load',
                'VMware UAG Appliance Total CPU Load in Percent',
                labels=self._label_names)
        }]

        self.metric_list_protocol = []

    def collect(self):
        self._create_metric_list()

        uag_data = UAG.get_data()
        if uag_data is None:
            return

        uag_data = uag_data['accessPointStatusAndStats']

        for metric in self.metric_list:
            try:
                _data = get_nested_item(uag_data, metric['path'])
            except KeyError:
                continue

            if type(_data) is not list:
                _data = [_data]

            if type(metric['metric']) is GaugeMetricFamily:
                for _d in _data:
                    if 'label' in metric:
                        labels = [get_nested_item(uag_data, metric['label'])]
                    else:
                        labels = []

                    if 'rlabel' in metric:
                        for _l in metric['rlabel']:
                            labels.append(_d[_l])
                    if 'rdata' in metric:
                        _d = _d[metric['rdata']]
                    metric['metric'].add_metric(labels, float(_d))
                yield metric['metric']

            elif type(metric['metric']) is CounterMetricFamily:
                for _d in _data:
                    labels = []
                    if 'rlabel' in metric:
                        for _l in metric['rlabel']:
                            labels.append(_d[_l])
                    if 'rdata' in metric:
                        _d = _d[metric['rdata']]
                    metric['metric'].add_metric(labels, int(_d))
                yield metric['metric']

            elif type(metric['metric']) is InfoMetricFamily:
                for _d in _data:
                    labels = []
                    if 'rlabel' in metric:
                        for _l in metric['rlabel']:
                            labels.append(_d[_l])
                    if 'rdata' in metric:
                        _d = _d[metric['rdata']]

                    if type(_d) is not dict:
                        _d = {metric['label']: _d}

                    metric['metric'].add_metric(
                        labels,
                        {key: str(val) for key, val in _d.items()}
                    )
                yield metric['metric']


class MyRequestHandler(MetricsHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlsplit(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)

        if "target" in query:
            host = query['target'][0]
            UAG.get_monitor(host)
            return super(MyRequestHandler, self).do_GET()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"No target defined\n")


def main():
    REGISTRY.register(UAGExporter())

    server_address = ('', 19000)
    HTTPServer(server_address, MyRequestHandler).serve_forever()


if __name__ == '__main__':
    main()
