import uuid
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from pypalettes import load_cmap


class HighChartBase:
    def __init__(self, 
                 data, 
                 tittel: str = " ", 
                 undertittel: str = " ", 
                 y_akse_tekst: str = " "
                 ):
        self.data = data
        self.tittel = tittel
        self.undertittel = undertittel
        self.y_akse_tekst = y_akse_tekst
        self.diagram_id = str(uuid.uuid4())
        self.innstillinger = self.definer_innstillinger()

    def lag_diagram(self):
        diagram = Chart(options=self.innstillinger)
        diagram.display()


class KolonneDiagram(HighChartBase): 
    def definer_innstillinger(self):
        innstillinger = HighchartsOptions(
            chart={'renderTo': self.diagram_id, 'type': 'column'},
            title={'text': self.tittel},
            subtitle={'text': self.undertittel},
            x_axis={'categories': self.data.svar_alternativer},
            y_axis={'title': {'text': self.y_akse_tekst}},
            series=self.data.dataserier,
            credits={'enabled': False}
            )
        return innstillinger


class StabletKolonneDiagram(HighChartBase):
    def definer_innstillinger(self):
        innstillinger = HighchartsOptions(
            chart={'renderTo': self.diagram_id, 'type': 'column'},
            title={'text': self.tittel},
            subtitle={'text': self.undertittel},
            x_axis={'categories': self.data.x_axis_labels or self.data.kolonner},
            y_axis={'title': {'text': self.y_akse_tekst}},
            series=self.data.dataserier,
            credits={'enabled': False},
            plot_options={'column': {'stacking': 'percent', 'dataLabels': {'enabled': True, 'format': '{point.percentage:.0f}%'}}},
            tooltip={'pointFormat': '<span style="color:{point.color}">{series.name}</span>: <b>{point.percentage:.1f}%</b> <br>Antall: {point.y:.0f}'}
        )
        return innstillinger
    

class ParallellDiagram(HighChartBase):
    def definer_innstillinger(self):
        y_axis = []
        for kolonne in self.data.kolonner:
            if kolonne in self.data.svar_alternativer:
                kategorier = self.data.svar_alternativer[kolonne]
                y_axis.append({'categories': kategorier,
                'tickPositions': [x for x, _ in enumerate(kategorier)],
                    } )
            else:
                kategorier = list(self.data.respons_mapping.keys())
                y_axis.append({'categories': [str(cat) for cat in kategorier],
                    } )
        


        innstillinger = HighchartsOptions(
            chart={
                'renderTo': self.diagram_id,
                'type': 'spline',
                'parallelCoordinates': True,
                'parallelAxes': {
                    'lineWidth': 2,
                },
                },
            title={'text': self.tittel},
            plot_options={
                'series': {
                    'allowPointSelect': False,
                    'lineWidth': 2,
                    'states': {
                        'inactive': {
                            'opacity': 0.1,
                        },
                    },
                    'point': {
                        'events': {
                            'mouseOver': '''function() {
                                var series = this.series.chart.series,
                                    x = this.x,
                                    y = this.y;

                                Highcharts.each(series, function(s) {
                                    if (s.data[x].y === y) {
                                        s.setState('hover');
                                    } else {
                                        s.setState('inactive');
                                    }
                                });
                            }''',
                            'mouseOut': '''function() {
                                var series = this.series.chart.series;
                                Highcharts.each(series, function(s) {
                                    s.setState('');
                                });
                            }''',
                        }
                    }
                }
            },
            tooltip={'pointFormat': """<span style="color:{point.color}; font-size: 10">\\u25CF</span><b>{point.formattedValue}</b>"""},
            x_axis={'categories': self.data.kolonner, 'offset': 10},
            y_axis=y_axis,
            colors=['rgba(11, 200, 200, 0.06)'],
            credits={'enabled': False},
            series=self.data.dataserier,
        )
        return innstillinger
    

class IndikatorDiagram(HighChartBase):
    def definer_innstillinger(self):
        farger = load_cmap("flattastic_flatui").colors
        innstillinger = HighchartsOptions(
            chart={'renderTo': self.diagram_id, 'type': 'solidgauge'},
            title={'text': self.tittel},
            subtitle={'text': self.undertittel, 'y': 90},
            pane={'background': 
                  {'backgroundColor': '#fff', 'innerRadius': '90%', 'outerRadius': '120%', 'shape': 'arc'}, 
                  'center': ['50%', '70%'], 'endAngle': 90, 'startAngle': -90},
            series=self.data.dataserier,
            tooltip={'enabled': False},
            y_axis={
                'labels': {'distance': 40}, 'max': 10, 'min': 0, 'stops': [
                    [0.0, farger[0]],  
                    [0.4, farger[2]], 
                    [0.7, farger[3]]], 
                'minorTickInterval': 20,
                'tickAmount': 6,
                'tickLength': '-40',
                'tickWidth': 0,
                'visible': True,
                'title': {'y': -70},
                'lineColor': 'white'
            },
            credits={'enabled': False}
        )
        return innstillinger
    

class PieDiagram(HighChartBase):

    def definer_innstillinger(self):
        innstillinger = HighchartsOptions(
            chart={'renderTo': self.diagram_id, 'type': 'pie'},
            title={'text': self.tittel},
            subtitle={'text': self.undertittel},
            series=self.data.dataserier,
            credits={'enabled': False},
            plot_options={
        'tooltip': {'value_suffix': '%', 'value_decimals': '1'},
        'type': 'pie',
        'name': 'Andel',
        'colorByPoint': True,
        'allowPointSelect': True,
        'cursor': 'pointer',
        'dataLabels': [{
            'enabled': True,
            'distance': 20
        }, {
            'enabled': True,
            'distance': -40,
            'format': '{point.percentage:.1f}%',
            'style': {
                'fontSize': '1.2em',
                'textOutline': 'none',
                'opacity': 0.7
            },
            'filter': {
                'operator': '>',
                'property': 'percentage',
                'value': 10
            }
        }],
        'showInLegend': True,
    },
            tooltip= {'value_suffix': '%', 'value_decimals': '1'},
        )
        return innstillinger
    

class BulletDiagram(HighChartBase):
    def definer_innstillinger(self):
        options = HighchartsOptions(
            chart={'renderTo': self.diagram_id, 
                   'inverted': True, 
                   'margin_left': 135, 
                   'margin_right': 100, 
                   'type': 'bullet'},
            title={'text': self.tittel},
            legend={'enabled': False},
            y_axis={'grid_line_width': 0.5, 
                    'min': 0, 
                    'max': 5, 
                    'tick_interval': 1, 
                    'title': {'text': ''}, 
                    'labels': {'formatter': "function() { return '⭐'.repeat(Math.floor(this.value)); }"}},
            credits={'enabled': False},
            exporting={'enabled': False},
            x_axis={'categories': self.data.x_axis_categories},
            series=[{'data': self.data.dataserier}],
            tooltip={'point_format': '<b>{point.y:.2f}</b> av {point.target}'}
        )
        return options


class JitterKommentarDiagram(HighChartBase):
    def definer_innstillinger(self):
        options = HighchartsOptions(
            chart={'renderTo': self.diagram_id, 'type': 'scatter'},
            title={'text': self.tittel},
            subtitle={'text': self.undertittel},
            legend={'enabled': True},
            credits={'enabled': False},
            x_axis={
                'title': {'text': 'Polaritet'},
                'categories': [0, 'Positive', 'Mixed', 'Negative', 'Neutral']
            },
            y_axis={
                'title': {'text': ' '},
                'labels': {'enabled': False}
            },
            series=self.data.dataserier
        )
        return options



class KommentarDiagram(HighChartBase):
    def definer_innstillinger(self):
        options = HighchartsOptions(
            chart={'renderTo': self.diagram_id, 'type': 'scatter'},
            title={'text': self.tittel},
            subtitle={'text': self.undertittel},
            legend={'enabled': False},
            credits={'enabled': False},
            x_axis={
                'title': {'text': ' '},
                'labels': {'enabled': False},
                'gridLineWidth': 0,
                'lineWidth': 0,
                'tickLength': 0
            },
            y_axis={
                'title': {'text': ' '},
                'labels': {'enabled': False},
                'gridLineWidth': 0,
                'lineWidth': 0.
            },
            tooltip={
                'pointFormat': '{point.kommentar}'
            },
            series=self.data.dataserier
        )
        return options