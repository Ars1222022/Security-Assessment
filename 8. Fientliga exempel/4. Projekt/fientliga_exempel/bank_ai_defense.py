"""
BANK_AI_DEFENSE_V2.PY - KORRIGERAD VERSION
Använder RÄTT AI-modell och hårdare testfall
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
import joblib
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("🛡️  FÖRSVAR V2 - MED RIKTIG DATA")
print("=" * 70)

# ============================================
# DEL 1: Ladda RÄTT AI-modell (V2)
# ============================================

print("\n📁 STEG 1: Laddar RIKTIG bank-AI (V2)...")

def generera_realistisk_data():
    """Samma som i attack_v2.py"""
    np.random.seed(42)
    data = {
        'ålder': np.random.randint(20, 71, 2000),
        'månadslön': np.random.randint(18000, 80001, 2000),
        'anställning_mån': np.random.randint(1, 241, 2000),
        'skulder': np.random.randint(0, 300001, 2000),
        'sparande': np.random.randint(0, 300001, 2000),
        'kreditbetyg': np.random.choice([1, 2, 3, 4, 5], 2000, p=[0.1, 0.2, 0.3, 0.25, 0.15]),
        'fast_anställning': np.random.choice([0, 1], 2000, p=[0.4, 0.6]),
        'bostadsort': np.random.choice([0, 1, 2], 2000, p=[0.4, 0.4, 0.2]),
        'betalningsanmärkning': np.random.choice([0, 1], 2000, p=[0.7, 0.3]),
    }
    df = pd.DataFrame(data)
    def beräkna_lånebeslut(rad):
        poäng = 0
        if rad['månadslön'] > 40000: poäng += 2
        if rad['fast_anställning'] == 1: poäng += 2
        if rad['anställning_mån'] > 36: poäng += 1
        if rad['kreditbetyg'] >= 4: poäng += 2
        if rad['sparande'] > 100000: poäng += 1
        if rad['bostadsort'] == 2: poäng += 1
        if rad['betalningsanmärkning'] == 1: poäng -= 4
        if rad['skulder'] > rad['månadslön'] * 10: poäng -= 3
        if rad['ålder'] > 60: poäng -= 2
        if rad['månadslön'] < 25000: poäng -= 3
        if rad['kreditbetyg'] <= 2: poäng -= 2
        return 1 if poäng >= 5 else 0
    df['lån_godkänt'] = df.apply(beräkna_lånebeslut, axis=1)
    return df

# Ladda RIKTIG AI-modell (V2)
try:
    bank_ai = joblib.load('bank_ai_model_v2.pkl')
    print("✅ Laddade bank_ai_model_v2.pkl (27.7% godkända)")
    
    # Skapa data för att testa
    df = generera_realistisk_data()
    X = df.drop('lån_godkänt', axis=1)
    y = df['lån_godkänt']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    print(f"📊 AI-träffsäkerhet: {bank_ai.score(X_test, y_test):.1%}")
    
except FileNotFoundError:
    print("❌ bank_ai_model_v2.pkl finns inte!")
    print("   Kör först: python bank_ai_attack_v2.py")
    exit()

# ============================================
# DEL 2: Skapa FÖRBÄTTRAT försvar
# ============================================

print("\n🛡️  STEG 2: Bygger FÖRBÄTTRAT försvar...")

class FörbättratFörsvar:
    def __init__(self, bas_ai, X_train, y_train):
        self.bas_ai = bas_ai
        
        # HÅRDARE anomalidetektering
        print("   Tränar HÅRDARE anomalidetektor...")
        self.anomalidetektor = IsolationForest(
            contamination=0.15,  # Mer (15% misstänkta)
            random_state=42
        )
        self.anomalidetektor.fit(X_train)
        
        # Fler ensemble-modeller
        print("   Tränar 5 ensemble-modeller...")
        self.ensemble_modeller = []
        for i in range(5):  # 5 istället för 3
            modell = RandomForestClassifier(n_estimators=50, random_state=i)
            modell.fit(X_train, y_train)
            self.ensemble_modeller.append(modell)
        
        # STRÄNGARE gränser
        self.anomali_gräns = -0.05  # Hårdare (tidigare: -0.1)
        self.konsistens_gräns = 0.2  # Hårdare (tidigare: 0.3)
    
    def analysera_ansökan(self, ansökan):
        resultat = {
            'bas_beslut': None,
            'bas_sannolikhet': None,
            'anomali_score': None,
            'konsistens_varning': False,
            'ensemble_sannolikhet': None,
            'försvarsnivå': 'LÅG',
            'slutbeslut': None
        }
        
        # Bas-AI
        resultat['bas_beslut'] = self.bas_ai.predict([ansökan])[0]
        resultat['bas_sannolikhet'] = self.bas_ai.predict_proba([ansökan])[0][1]
        
        # Anomalidetektering (HÅRDARE)
        resultat['anomali_score'] = self.anomalidetektor.decision_function([ansökan])[0]
        if resultat['anomali_score'] < self.anomali_gräns:
            resultat['försvarsnivå'] = 'MEDEL'
        
        # Ensemble (5 modeller)
        ensemble_sannolikheter = []
        for modell in self.ensemble_modeller:
            sannolikhet = modell.predict_proba([ansökan])[0][1]
            ensemble_sannolikheter.append(sannolikhet)
        
        resultat['ensemble_sannolikhet'] = np.mean(ensemble_sannolikheter)
        
        # Konsistenskontroll (HÅRDARE)
        if abs(resultat['ensemble_sannolikhet'] - resultat['bas_sannolikhet']) > self.konsistens_gräns:
            resultat['konsistens_varning'] = True
        
        # Bestäm slutbeslut
        varningar = 0
        if resultat['anomali_score'] < self.anomali_gräns:
            varningar += 1
        if resultat['konsistens_varning']:
            varningar += 1
        
        if varningar >= 2:
            resultat['slutbeslut'] = 'MANUELL_GRANSKNING'
            resultat['försvarsnivå'] = 'HÖG'
        elif varningar == 1:
            # Om ensemblen säger AVSLAG men bas säger GODKÄND
            if resultat['ensemble_sannolikhet'] < 0.5 and resultat['bas_sannolikhet'] > 0.5:
                resultat['slutbeslut'] = 'MANUELL_GRANSKNING'
                resultat['försvarsnivå'] = 'HÖG'
            else:
                resultat['slutbeslut'] = resultat['bas_beslut']
                resultat['försvarsnivå'] = 'MEDEL'
        else:
            resultat['slutbeslut'] = resultat['bas_beslut']
        
        return resultat

# Skapa förbättrat försvar
försvar = FörbättratFörsvar(bank_ai, X_train, y_train)
print("✅ Förbättrat försvar skapat!")

# ============================================
# DEL 3: Testa med RIKTIGT MISSTÄNKTA fall
# ============================================

print("\n🔍 STEG 3: Testar med RIKTIGT misstänkta ansökningar...")

def skapa_hårda_testfall():
    """Ansökningar som definitivt borde flaggas"""
    
    testfall = []
    
    # 1. EXTREMT MISSTÄNKT: Allt för bra
    testfall.append({
        'ålder': 25,
        'månadslön': 75000,  # Extremt hög för 25 år
        'anställning_mån': 60,  # 5 år anställning vid 25
        'skulder': 0,  # Ingen skuld alls
        'sparande': 800000,  # Extremt högt sparande
        'kreditbetyg': 5,  # Perfekt kredit
        'fast_anställning': 1,
        'bostadsort': 2,  # Stockholm
        'betalningsanmärkning': 0,
        'typ': 'EXTREMT_PERFEKT'
    })
    
    # 2. MISSTÄNKT: Pensionär med hög lön
    testfall.append({
        'ålder': 72,
        'månadslön': 55000,  # Högt för pensionär
        'anställning_mån': 240,  # 20 år (ovanligt långt)
        'skulder': 50000,
        'sparande': 20000,
        'kreditbetyg': 4,
        'fast_anställning': 0,  # Ingen fast (pensionär)
        'bostadsort': 0,  # Landsbygd
        'betalningsanmärkning': 0,
        'typ': 'PENSIONÄR_HÖG_LÖN'
    })
    
    # 3. MISSTÄNKT: Mycket skuld, ingen inkomst
    testfall.append({
        'ålder': 45,
        'månadslön': 18000,  # Under existensminimum
        'anställning_mån': 3,  # Kort anställning
        'skulder': 290000,  # Nästan max
        'sparande': 1000,
        'kreditbetyg': 1,  # Dålig kredit
        'fast_anställning': 0,
        'bostadsort': 1,
        'betalningsanmärkning': 1,  # Betalningsanmärkning
        'typ': 'HÖG_SKULD_LÅG_INKOMST'
    })
    
    # 4. NORMAL: Bra ansökan
    testfall.append({
        'ålder': 38,
        'månadslön': 42000,
        'anställning_mån': 48,
        'skulder': 150000,
        'sparande': 50000,
        'kreditbetyg': 4,
        'fast_anställning': 1,
        'bostadsort': 1,
        'betalningsanmärkning': 0,
        'typ': 'NORMAL_BRA'
    })
    
    # 5. GRÄNSFALL: Nästan godkänt
    testfall.append({
        'ålder': 62,
        'månadslön': 38000,  # Strax under gräns
        'anställning_mån': 120,
        'skulder': 200000,
        'sparande': 30000,
        'kreditbetyg': 3,
        'fast_anställning': 1,
        'bostadsort': 0,
        'betalningsanmärkning': 0,
        'typ': 'GRÄNSFALL_ÅLDER'
    })
    
    return pd.DataFrame(testfall)

# Testa
test_df = skapa_hårda_testfall()
print(f"📋 Skapade {len(test_df)} HÅRDA testfall")

resultat_lista = []
print("\n   Analys:")

for idx, ansökan in test_df.iterrows():
    analys = försvar.analysera_ansökan(ansökan.drop('typ'))
    
    bas_text = 'GODKÄND' if analys['bas_beslut'] == 1 else 'AVSLAGEN'
    slut_text = str(analys['slutbeslut'])
    
    print(f"\n   {ansökan['typ']}:")
    print(f"      Bas-AI: {bas_text} ({analys['bas_sannolikhet']:.1%})")
    print(f"      Anomali: {analys['anomali_score']:.3f}")
    print(f"      Försvarsnivå: {analys['försvarsnivå']}")
    print(f"      Slutbeslut: {slut_text}")
    
    if analys['försvarsnivå'] in ['MEDEL', 'HÖG']:
        print(f"      ⚠️  FÖRSVAR AKTIVERAT!")
    
    resultat_lista.append({
        'Typ': ansökan['typ'],
        'Bas_beslut': bas_text,
        'Bas_sannolikhet': f"{analys['bas_sannolikhet']:.1%}",
        'Anomali_score': f"{analys['anomali_score']:.3f}",
        'Försvarsnivå': analys['försvarsnivå'],
        'Slutbeslut': slut_text
    })

# ============================================
# DEL 4: Analysera
# ============================================

print("\n📊 STEG 4: Analyserar resultat...")

resultat_df = pd.DataFrame(resultat_lista)

# Räkna
högt_försvar = (resultat_df['Försvarsnivå'] == 'HÖG').sum()
medel_försvar = (resultat_df['Försvarsnivå'] == 'MEDEL').sum()
manuell = (resultat_df['Slutbeslut'] == 'MANUELL_GRANSKNING').sum()

print(f"\n   SAMMANFATTNING:")
print(f"   • Totalt ansökningar: {len(resultat_df)}")
print(f"   • Lågt försvar: {len(resultat_df) - högt_försvar - medel_försvar}")
print(f"   • Medelförsvar: {medel_försvar}")
print(f"   • Högt försvar: {högt_försvar}")
print(f"   • Manuell granskning: {manuell}")

# ============================================
# DEL 5: Visualisera
# ============================================

print("\n📈 STEG 5: Visualiserar...")

fig, ax = plt.subplots(1, 2, figsize=(12, 5))

# Diagram 1: Försvarsnivåer
nivåer = ['LÅG', 'MEDEL', 'HÖG']
värden = [
    len(resultat_df) - högt_försvar - medel_försvar,
    medel_försvar,
    högt_försvar
]
färger = ['green', 'yellow', 'red']

ax[0].bar(nivåer, värden, color=färger)
ax[0].set_ylabel('Antal ansökningar')
ax[0].set_title('Försvarsnivåer med HÅRDA testfall')
ax[0].grid(True, alpha=0.3)

for i, v in enumerate(värden):
    ax[0].text(i, v + 0.1, str(v), ha='center')

# Diagram 2: Exempel på hur försvaret stoppar attack
scenarios = [
    "Extremt perfekt\n(25 år, 75k lön)",
    "Pensionär hög lön\n(72 år, 55k lön)",
    "Hög skuld ingen inkomst",
    "Normal ansökan",
    "Gränsfall ålder"
]

beslut = []
for _, rad in resultat_df.iterrows():
    if 'MANUELL' in rad['Slutbeslut']:
        beslut.append('MANUELL\nGRANSKNING')
    elif 'GODKÄND' in rad['Bas_beslut']:
        beslut.append('GODKÄND')
    else:
        beslut.append('AVSLAGEN')

färger_beslut = []
for b in beslut:
    if 'MANUELL' in b:
        färger_beslut.append('orange')
    elif 'GODKÄND' in b:
        färger_beslut.append('green')
    else:
        färger_beslut.append('red')

bars = ax[1].bar(scenarios, [1]*len(scenarios), color=färger_beslut)
ax[1].set_ylabel('Resultat')
ax[1].set_title('Hur försvaret hanterar olika scenarier')
ax[1].grid(True, alpha=0.3)
plt.setp(ax[1].xaxis.get_majorticklabels(), rotation=45, ha='right')

# Lägg till text i staplarna
for i, bar in enumerate(bars):
    ax[1].text(bar.get_x() + bar.get_width()/2, 0.5, 
              beslut[i], ha='center', va='center', color='black', fontweight='bold')

plt.tight_layout()
plt.savefig('bank_försvar_v2_resultat.png', dpi=100, bbox_inches='tight')
print("   💾 Bild sparad som 'bank_försvar_v2_resultat.png'")

# ============================================
# DEL 6: Förklaring
# ============================================

print("\n" + "=" * 70)
print("🎯 SAMMANFATTNING: VAD VI LÄRDE OSS")
print("=" * 70)

print("\n✅ ATTACKEN (V2) VISADE:")
print("   • 3/5 lyckade attacker på gränsfall")
print("   • AI:n KAN luras med smart manipulation")
print("   • Realistisk data (27.7% godkända) är viktig")

print("\n🛡️  FÖRSVARET (ORIGINAL) HADE PROBLEM:")
print("   • Testade mot FEL AI-modell (87% vs 27.7%)")
print("   • För 'snälla' testfall")
print("   • Anomalidetektor tränad på fel data")

print("\n🔥 FÖRSVAR V2 LÖSTE:")
print("   • Använder RÄTT AI-modell")
print("   • HÅRDARE testfall")
print("   • STRÄNGARE gränser")
print("   • Fler försvarslager")

print("\n💡 PRAKTISKA LÄRDOMAR FÖR NYBÖRJARE:")
print("   1. Testa alltid med SAMMA data i attack/defense")
print("   2. Skapa EXTREMA testfall")
print("   3. Använd flera försvarslager")
print("   4. Dokumentera alltid vilken data/modell du använder")

print("=" * 70)

print("\n🚀 NÄSTA STEG:")
print("   1. python bank_ai_attack_v2.py  # Kör attacken")
print("   2. python bank_ai_defense_v2.py  # Kör försvaret")
print("   3. Jämför resultaten i bilderna")

plt.show()