import pandas as pd
import numpy as np
from pypalettes import load_cmap
from typing import List, Dict
import pickle
import random


class HighChartData:
    def __init__(self, 
                 filnavn: str = None, 
                 kilde: str = None,
                 df: pd.DataFrame = None,
                 kolonner: List[str] = None, 
                 svar_alternativer: List[str] = None,
                 x_axis_labels: List[str] = None,
                 tilfeldige_farger: bool = None,
                 farger_seed: int = None
                 ):
        self.kilde = kilde
        self.df = df
        self.filnavn = filnavn
        self.kolonner = kolonner
        self.svar_alternativer = svar_alternativer
        self.x_axis_labels = x_axis_labels or kolonner
        self.tilfeldige_farger = tilfeldige_farger
        self.farger_seed = farger_seed
        self.dataserier = self.lag_dataserier()

    def normaliser_kolonne(self, kolonne_navn):
        return (
            kolonne_navn
            .strip()
            .lower()
            .replace(' ', '_')
            .replace('\xa0', '_')
            .replace('\n', '')
        )
    
    def les_df(self) -> pd.DataFrame:
        df_selected = self.df[self.kolonner]
        return df_selected
        

    def les_excel(self) -> pd.DataFrame:
        df = pd.read_excel(io=self.filnavn, engine='openpyxl')
        df.columns = [self.normaliser_kolonne(kol) for kol in df.columns]
        self.normaliserte_kolonner = [self.normaliser_kolonne(kol) for kol in self.kolonner]

        df_selected = df[self.normaliserte_kolonner]
        df_selected.columns = self.kolonner
        return df_selected
    
    def tell_antall(self, df: pd.DataFrame) -> Dict[str, List[int]]:
        antall = {}
        for kolonne in self.kolonner:
            telling = (
                df[kolonne]
                .astype(str)
                .value_counts()
                .reindex(self.svar_alternativer, fill_value=0)
            )
            antall[kolonne] = telling.tolist()
        return antall
    
    def langt_format(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.reset_index(names='idx')
        df_lang = df.melt(id_vars=['idx'],
                          value_vars=self.kolonner, 
                          var_name='Spørsmål', 
                          value_name='Svar')
        return df_lang
    
    def get_colors(self, num_colors: int) -> List[str]:
        # Added method to handle color assignment
        if self.farger_seed is not None:
            np.random.seed(self.farger_seed)
        if self.tilfeldige_farger:
            colors = np.random.choice(load_cmap("flattastic_flatui").colors, num_colors, replace=False).tolist()
        else:
            colors = [load_cmap("flattastic_flatui").colors[i % len(load_cmap("flattastic_flatui").colors)] for i in range(num_colors)]
        return colors


class KolonneData(HighChartData):
    
    def lag_dataserier(self) -> List[Dict]:
        if self.kilde == 'excel':
            df = self.les_excel()
        elif self.kilde == 'df':
            df = self.les_df()
        else:
            raise ValueError(f"Invalid kilde: {self.kilde}. Expected 'excel' or 'df'.")
        antall = self.tell_antall(df)
        formatert_data = []

        for kolonne, label, data in zip(antall.keys(), self.x_axis_labels, antall.values()):
            colors = self.get_colors(len(data))  # Changed to use get_colors method
            data_with_colors = [{'y': value, 'color': colors[i]} for i, value in enumerate(data)]

            formatert_data.append({
                'name': label,
                'type': 'column',
                'data': data_with_colors,
            })
        return formatert_data
    
class StabletKolonneData(HighChartData):
    def lag_dataserier(self) -> List[Dict]:
        if self.kilde == 'excel':
            df = self.les_excel()
        elif self.kilde == 'df':
            df = self.les_df()
        else:
            raise ValueError(f"Invalid kilde: {self.kilde}. Expected 'excel' or 'df'.")

        antall = self.tell_antall(df)
        formatert_data = []

        colors = self.get_colors(len(self.svar_alternativer))  # Generate colors for all svar_alternativer

        for svar in self.svar_alternativer:
            data = [antall[kolonne][self.svar_alternativer.index(svar)] for kolonne in self.kolonner]
            color = colors[self.svar_alternativer.index(svar) % len(colors)]  # Assign unique color to each svar

            formatert_data.append({
                'name': svar,
                'type': 'column',
                'data': data,
                'stack': 'Svar',
                'color': color
            })

        return formatert_data


class ParallellData(HighChartData):
    def __init__(self, filnavn: str, kolonner: List[str], svar_alternativer: Dict[str, List[str]] = None, tilfeldige_farger: bool = None, farger_seed: int = None):
        self.svar_alternativer = svar_alternativer or {}
        super().__init__(filnavn, kolonner, self.svar_alternativer, tilfeldige_farger=tilfeldige_farger, farger_seed=farger_seed)

    def langt_format(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.reset_index(names='idx')
        df_lang = df.melt(id_vars=['idx'],
                          value_vars=self.kolonner, 
                          var_name='Spørsmål', 
                          value_name='Svar')
        return df_lang
    
    def map_responser_til_verdier(self, df_lang):
        respons_mapping = {}
        for kolonne in self.kolonner:
            if kolonne in self.svar_alternativer:
                categories = self.svar_alternativer[kolonne]
            else:
                categories = df_lang[df_lang['Spørsmål'] == kolonne]['Svar'].unique()
            for idx, response in enumerate((categories)):
                respons_mapping[response] = idx
        
        df_lang['MappedSvar'] = df_lang['Svar'].astype(str).map(respons_mapping)
        self.respons_mapping = respons_mapping
        return df_lang, respons_mapping
    
    def generer_parallell_koordinat_data(self, df_lang_med_mapping):
        parallel_coordinates_data = []
        for _, group in df_lang_med_mapping.groupby('idx'):
            mapped_svar_list = group['MappedSvar'].tolist()
            parallel_coordinates_data.append(mapped_svar_list)
        
        return parallel_coordinates_data

    def lag_dataserier(self) -> List[Dict]:
        if self.kilde == 'excel':
            df = self.les_excel()
        elif self.kilde == 'df':
            df = self.les_df()
        else:
            raise ValueError(f"Invalid kilde: {self.kilde}. Expected 'excel' or 'df'.")
        df = self.langt_format(df)
        df, self.respons_mapping = self.map_responser_til_verdier(df)
        data = self.generer_parallell_koordinat_data(df)
        formatert_data = []
        for i in range(len(data)):
            formatert_data.append({
                'name': 'Svar ' + str(i),
                'data': data[i],
            })
        return formatert_data
    

class IndikatorData(HighChartData):
    
    def finn_gjennomsnitt(self, df: pd.Series) -> float:
        return  df.mean().values[0]

    def lag_dataserier(self) -> List[Dict]:
        if self.kilde == 'excel':
            df = self.les_excel()
        elif self.kilde == 'df':
            df = self.les_df()
        else:
            raise ValueError(f"Invalid kilde: {self.kilde}. Expected 'excel' or 'df'.")
        gj_snitt = self.finn_gjennomsnitt(df)

        formatert_data = [{
                'data': gj_snitt,
                'dataLabels': {
                    'y': -30,
                    'x': 0,
                    'borderWidth': 0,
                    'format':                 
                    '<div style="display: flex; flex-direction: column; align-items: center; border: 1px solid red;">' +
                    '<span style="font-size:70px; display: block; border: 1px solid blue;">{y:.1f}</span><br/>' +
                    '</div>'
                    },
                'innerRadius': '90%',
                'radius': '120%'
            }]
        return formatert_data
    

class PieData(HighChartData):

    def finn_andel(self, df):
        df = self.langt_format(df)

        df['Svar'] = df['Svar'].apply(lambda x: x if x in self.svar_alternativer else 'Annet')

        df_andel = df.groupby('Svar').agg(Antall=('Svar', 'count')).reset_index()

        
        df_andel['Prosent'] = (df_andel['Antall'] / df_andel['Antall'].sum()) * 100
        df_andel['Prosent'] = df_andel['Prosent'].fillna(0)
        df_andel['Svar'] = pd.Categorical(df_andel['Svar'], categories=self.svar_alternativer + ['Annet'], ordered=True)
        df_andel = df_andel.sort_values('Svar')

        data = df_andel[['Svar', 'Prosent']].rename(columns={'Svar': 'name', 'Prosent': 'y'}).to_dict(orient='records')
        return data

    def lag_dataserier(self) -> List[Dict]:
        if self.kilde == 'excel':
            df = self.les_excel()
        elif self.kilde == 'df':
            df = self.les_df()
        else:
            raise ValueError(f"Invalid kilde: {self.kilde}. Expected 'excel' or 'df'.")
        data = self.finn_andel(df)
        formatert_data = [{
            'tooltip': {'value_suffix': '%', 'value_decimals': '1'},
            'type': 'pie',
            'name': 'Andel',
            'colorByPoint': True,
            'data': data,
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
            'showInLegend': False,
        }]
        return formatert_data


class BulletData(HighChartData):
    def __init__(self, filnavn: str, kolonner: List[str], svar_alternativer: List[str], x_axis_categories: List[str] = None):
        self.x_axis_categories = x_axis_categories or kolonner
        super().__init__(filnavn, kolonner, svar_alternativer)

    def gjennomsnitt_per_kolonne(self, df, spoersmaal):
        df_spoersmaal = df[df['Spørsmål'] == spoersmaal]
        return df_spoersmaal['Svar'].mean()

    def lag_dataserier(self) -> List[Dict]:
        if self.kilde == 'excel':
            df = self.les_excel()
        elif self.kilde == 'df':
            df = self.les_df()
        else:
            raise ValueError(f"Invalid kilde: {self.kilde}. Expected 'excel' or 'df'.")
        df_long = self.langt_format(df)
        df_long['Svar'] = pd.to_numeric(df_long['Svar'], errors='coerce')

        gj_snitt = [self.gjennomsnitt_per_kolonne(df_long, q) for q in self.kolonner]
        farger = load_cmap("flattastic_flatui").colors

        dataserier = [{'y': gj_snitt[i] if not pd.isna(gj_snitt[i]) else 0, 
                        'target': 5, 'color': farger[5]} 
                        for i in range(len(self.kolonner))]
        return dataserier


class JitterKommentarData(HighChartData):
    def __init__(self, 
                 kilde: str = None,
                 df: str = None,
                 filnavn: str = None, 
                 kolonner: Dict[str, str] = None,
                 svar_alternativer: List[str] = None):
        self.kilde = kilde       
        self.svar_alternativer = svar_alternativer
        self.kolonner = kolonner or {}
        self.label = self.kolonner.get('label', 'label')
        self.kommentar = self.kolonner.get('kommentar', 'kommentar')
        self.df = df
        self.df = self.get_df()
        self.dataserier = self.lag_dataserier()

    def get_df(self):
        if self.kilde == 'pickle':
            df = self.df_from_pickle
        elif self.kilde == 'df':
            df = self.df
        else:
            raise ValueError(f"Invalid kilde: {self.kilde}. Expected 'pickle' or 'df'.")
        return df

    def df_from_pickle(self, filnavn):
        with open(filnavn, 'rb') as f:
            df = pickle.load(f)
        return df

    def lag_jitter_data(self, df, x_value):
        jitter_data = []
        for _, row in df.iterrows():
            jitter_x = x_value + (0.7 * (0.5 - np.random.rand()))
            jitter_y = np.random.rand()
            jitter_data.append({
                'x': jitter_x,
                'y': jitter_y, 
                'custom': {
                    'kommentar': row[self.kommentar],
                }
            })
        return jitter_data

    def lag_dataserier(self) -> List[Dict]:
        df = self.df
        colors = load_cmap("flattastic_flatui").colors
        colors = [colors[3], colors[2], colors[1], colors[6]]
        dataserie = []

        # Check if the DataFrame is empty
        if df.empty:
            print("The DataFrame is empty. No data to process.")
            return dataserie

        # Check if the expected columns are present
        if self.label not in df.columns:
            print(f"The DataFrame does not contain the expected column '{self.label}'.")
            return dataserie

        for i, label in enumerate(self.svar_alternativer):
            # Ensure the colors list is correctly indexed
            color = colors[i % len(colors)]

            df_filtered = df[df[self.label] == label]
            jitter_data = self.lag_jitter_data(df_filtered, i + 1)
            dataserie.append({
                'name': f'{label}',
                'type': 'scatter',
                'data': jitter_data,
                'marker': {
                    'radius': 5,
                    'symbol': 'circle'
                },
                'color': color,
                'tooltip': {
                    'pointFormat': '{point.custom.kommentar}'
                },
            })
        return dataserie
    

class KommentarData(HighChartData):
    def __init__(self, 
                 filnavn: str = None, 
                kolonner: Dict[str, str] = None,
                svar_alternativer: List[str] = None,
                kilde: str = None,
                df: pd.DataFrame = None):
        self.filnavn = filnavn
        self.svar_alternativer = svar_alternativer
        self.kolonner = kolonner
        self.kilde = kilde
        self.df = df
        self.dataserier = self.lag_dataserier()
    
    def formater_kommentar_linjeskift(self, comment, max_length=50):
        if not isinstance(comment, str):
            return comment  # Return the original value if it's not a string
        words = comment.split() # Split into words
        formatted_comment = ''
        current_line_length = 0
        for word in words:
            if current_line_length + len(word) + 1 > max_length:
                formatted_comment += '<br>' 
                current_line_length = 0  
            formatted_comment += word + ' '  
            current_line_length += len(word) + 1  
        return formatted_comment.strip()  

    def lag_dataserier(self) -> List[Dict]:
        if self.kilde == 'excel':
            df = self.les_excel()
        elif self.kilde == 'df':
            df = self.les_df()
        else:
            raise ValueError(f"Invalid kilde: {self.kilde}. Expected 'excel' or 'df'.")
        df = df.sample(frac=1).reset_index(drop=True)
        colors = load_cmap("flattastic_flatui").colors
        colors = [colors[6]]
        
        # Iterate over each column in kolonner and apply the formatting function
        for col in self.kolonner:
            df[col] = df[col].apply(lambda x: self.formater_kommentar_linjeskift(x))

        # Prepare data for Highcharts
        jitter_data = []
        for index, row in df.iterrows():
            for col in self.kolonner:
                jitter_data.append({
                    'svar_nr': int(index) + 1,
                    'x': random.random(),  
                    'y': random.random(),  
                'custom': {
                    'kommentar': row[col],
                }
                })


        # Create data series
        dataserie = []
        dataserie.append({
            'type': 'scatter',
            'data': jitter_data,
            'marker': {
                'radius': 5,
                'symbol': 'circle'
            },
            'color': colors[0],
            'tooltip': {
                'headerFormat': '<strong>Kommentar:</strong><br/>',
                'pointFormat': '{point.custom.kommentar}',
            },
        })

        return dataserie