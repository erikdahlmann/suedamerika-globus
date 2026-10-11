import json, sys
from shapely.geometry import shape, Polygon, mapping
S, P = sys.argv[1], sys.argv[2]
ISO = 'ARG BOL BRA CHL COL ECU GUY PRY PER SUR URY VEN'.split()
JAHRE = ['1980', '1990', '2000', '2010', '2024']
def wb(ind):
    d = json.load(open(f'{S}/w_{ind}.json'))[1]
    return {(r['countryiso3code'], r['date']): r['value'] for r in d}
quellen = {}  # (iso, key, idx) -> Hinweis
daten = {i: {} for i in ISO}
for key, ind, f in [('kopf','NY.GDP.PCAP.KD',1), ('bip','NY.GDP.MKTP.KD',1e-9), ('ew','SP.POP.TOTL',1e-6),
                    ('wachs','NY.GDP.MKTP.KD.ZG',1), ('infl','FP.CPI.TOTL.ZG',1), ('alq','SL.UEM.TOTL.ZS',1)]:
    m = wb(ind)
    for i in ISO:
        reihe = []
        for k, y in enumerate(JAHRE):
            yy = '1991' if key == 'alq' and y == '1990' else y
            v = m.get((i, yy))
            if key == 'alq' and y == '1990' and v is not None: quellen[f'{i}.alq.{k}'] = 'Wert von 1991, frühere Werte gibt es nicht'
            reihe.append(None if v is None else round(v * f, 2 if key in ('ew','wachs','infl','alq') else 1))
        daten[i][key] = reihe
# Inflationslücken: IWF WEO (aktuell, April 2026 über imf.org) und WEO Oktober 2010 für Argentinien 1980/1990
imf = {'VEN': [21.4, 40.7, 16.2, None, 49.4], 'BRA': [90.2, None, None, None, None], 'GUY': [14.1, 64.3, None, None, None],
       'ARG': [100.76, 2313.96, -0.94, 10.46, None]}
for i, r in imf.items():
    for k, v in enumerate(r):
        if daten[i]['infl'][k] is None and v is not None:
            daten[i]['infl'][k] = v
            quellen[f'{i}.infl.{k}'] = 'Quelle: IWF, World Economic Outlook Oktober 2010' if i == 'ARG' and k < 2 else 'Quelle: IWF, World Economic Outlook'
quellen['ARG.infl.3'] = 'Offizieller Wert (IWF). Die Statistik galt als geschönt, unabhängige Schätzungen lagen bei etwa 25 %.'
fehlt = [(i, key, JAHRE[k]) for i in ISO for key, r in daten[i].items() for k, v in enumerate(r) if v is None]
print('fehlt:', fehlt)

# Ecuadors Anspruch bis 1998: peruanisches Gebiet nördlich von Marañón und Amazonas (vereinfacht)
fluss = [(-79.05,-4.95),(-78.75,-5.25),(-78.6,-5.5),(-78.2,-5.0),(-77.8,-4.6),(-77.5,-4.45),(-77.0,-4.6),(-76.55,-4.83),
         (-76.0,-4.95),(-75.6,-5.0),(-75.2,-4.85),(-74.6,-4.6),(-74.0,-4.55),(-73.55,-4.48),(-73.4,-4.1),(-73.25,-3.75),
         (-72.9,-3.5),(-72.4,-3.45),(-71.85,-3.32),(-71.3,-3.45),(-70.9,-3.75),(-70.52,-3.88),(-70.2,-4.1),(-69.95,-4.22),(-69.5,-4.3)]
nord = Polygon(fluss + [(-69.5, 2), (-81, 2), (-81, -4.95)])
sa = json.loads(open(f'{P}/lib/suedamerika.js').read()[len('window.SUEDAMERIKA='):-1])
peru = next(shape(f['geometry']) for f in sa['features'] if f['properties']['iso'] == 'PER')
anspruch = peru.buffer(0).intersection(nord).buffer(0)
geo = max(getattr(anspruch, 'geoms', [anspruch]), key=lambda g: g.area).simplify(0.02)
ring = [[round(y, 3), round(x, 3)] for x, y in geo.exterior.coords]
import math
km2 = geo.area * 111.32**2 * math.cos(math.radians(-2.5))
print('Anspruch Fläche ca.', round(km2), 'km²', len(ring), 'Punkte')
out = {'jahre': [int(y) for y in JAHRE], 'daten': daten, 'hinweise': quellen, 'anspruchEcuador': ring}
open(f'{P}/lib/zeitreihe.js', 'w').write('window.ZEITREIHE=' + json.dumps(out, ensure_ascii=False) + ';')
