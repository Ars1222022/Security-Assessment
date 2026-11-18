"""
BANK_AI_ATTACK_V2.PY
Bättre attack som faktiskt fungerar!
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("🏦 FIENTLIG ATTACK V2 - NU FUNGERAR DET!")
print("=" * 70)

# ============================================
# DEL 1: Skapa MER REALISTISK data
# ============================================

print("\n📊 STEG 1: Genererar REALISTISK svensk data...")

def generera_realistisk_lånedata(antal=1000):
    """Skapar data där många får avslag - som i verkligheten"""
    
    np.random.seed(42)
    
    data = {
        # Mer realistiska åldrar och löner
        'ålder': np.random.randint(20, 71, antal),
        'månadslön': np.random.randint(18000, 80001, antal),  # Lägre max
        'anställning_mån': np.random.randint(1, 241, antal),
        'skulder': np.random.randint(0, 300001, antal),  # Lägre max
        'sparande': np.random.randint(0, 300001, antal),  # Lägre max
        'kreditbetyg': np.random.choice([1, 2, 3, 4, 5], antal, p=[0.1, 0.2, 0.3, 0.25, 0.15]),
        'fast_anställning': np.random.choice([0, 1], antal, p=[0.4, 0.6]),  # Färre fasta
        'bostadsort': np.random.choice([0, 1, 2], antal, p=[0.4, 0.4, 0.2]),  # Färre storstäder
        'betalningsanmärkning': np.random.choice([0, 1], antal, p=[0.7, 0.3]),  # Fler anmärkningar
    }
    
    df = pd.DataFrame(data)
    
    # STRÄNGARE regler för lånebeslut
    def beräkna_lånebeslut(rad):
        poäng = 0
        
        # Positiva faktorer (strängare)
        if rad['månadslön'] > 40000: poäng += 2
        if rad['fast_anställning'] == 1: poäng += 2
        if rad['anställning_mån'] > 36: poäng += 1  # 3 år krav
        if rad['kreditbetyg'] >= 4: poäng += 2
        if rad['sparande'] > 100000: poäng += 1
        if rad['bostadsort'] == 2: poäng += 1
        
        # Negativa faktorer (strängare)
        if rad['betalningsanmärkning'] == 1: poäng -= 4  # Hårdare straff
        if rad['skulder'] > rad['månadslön'] * 10: poäng -= 3
        if rad['ålder'] > 60: poäng -= 2  # Hårdare åldersdiskriminering
        if rad['månadslön'] < 25000: poäng -= 3
        if rad['kreditbetyg'] <= 2: poäng -= 2
        
        # Kräv mer poäng
        return 1 if poäng >= 5 else 0  # 5 poäng krav
    
    df['lån_godkänt'] = df.apply(beräkna_lånebeslut, axis=1)
    
    return df

# Generera data
df_original = generera_realistisk_lånedata(2000)
print(f"📈 Genererade {len(df_original)} låneansökningar")
print(f"📊 Andel godkända: {df_original['lån_godkänt'].mean():.1%}")  # Borde vara ~50%

# ============================================
# DEL 2: Träna AI med den nya datan
# ============================================

print("\n🤖 STEG 2: Tränar bankens AI-modell...")

X = df_original.drop('lån_godkänt', axis=1)
y = df_original['lån_godkänt']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

bank_ai = RandomForestClassifier(n_estimators=100, random_state=42)
bank_ai.fit(X_train, y_train)

train_score = bank_ai.score(X_train, y_train)
test_score = bank_ai.score(X_test, y_test)

print(f"📈 AI-träffsäkerhet på träningsdata: {train_score:.1%}")
print(f"📊 AI-träffsäkerhet på testdata: {test_score:.1%}")
print("✅ Bankens AI är tränad!")

# ============================================
# DEL 3: SMARTARE attackstrategi
# ============================================

print("\n🎯 STEG 3: Planerar SMARTARE attack...")
print("   Ny strategi: Hitta GRÄNSFALL och manipuler dem")

def hitta_gränsfall(X_test, y_test, bank_ai, antal=10):
    """Hittar ansökningar som är nära gränsen"""
    
    gränsfall = []
    
    for idx, ansökan in X_test.iterrows():
        sannolikhet = bank_ai.predict_proba([ansökan])[0][1]
        
        # Gränsfall: mellan 40% och 60% sannolikhet
        if 0.4 <= sannolikhet <= 0.6:
            gränsfall.append((idx, ansökan, sannolikhet, y_test[idx]))
        
        if len(gränsfall) >= antal:
            break
    
    return gränsfall

def smart_manipulation(original_ansökan, mål_sannolikhet=0.7):
    """Smart manipulation baserat på vad AI bryr sig om"""
    
    manipulerad = original_ansökan.copy()
    
    # Ta reda på vilka features som är viktigast
    # (I verkligheten: använd feature importance eller gradienter)
    
    # Strategi: Öka viktiga parametrar, minska negativa
    if manipulerad['månadslön'] < 40000:
        manipulerad['månadslön'] = min(manipulerad['månadslön'] * 1.25, 80000)
    
    if manipulerad['kreditbetyg'] < 4:
        manipulerad['kreditbetyg'] = min(manipulerad['kreditbetyg'] + 1, 5)
    
    if manipulerad['skulder'] > 100000:
        manipulerad['skulder'] = manipulerad['skulder'] * 0.8
    
    if manipulerad['ålder'] > 60:
        manipulerad['anställning_mån'] = manipulerad['anställning_mån'] * 1.3
    
    if manipulerad['fast_anställning'] == 0:
        manipulerad['fast_anställning'] = 1
    
    return manipulerad

# Hitta gränsfall
print("\n🔍 Hittar gränsfall (ansökningar nära beslutsgränsen)...")
gränsfall = hitta_gränsfall(X_test, y_test, bank_ai, antal=5)

if len(gränsfall) == 0:
    print("⚠️  Inga gränsfall hittades - testar med andra parametrar")
    # Fallback: ta de med lägst sannolikhet för godkännande
    test_probas = bank_ai.predict_proba(X_test)[:, 1]
    lägsta_idx = np.argsort(test_probas)[:5]
    gränsfall = [(X_test.index[i], X_test.iloc[i], test_probas[i], y_test.iloc[i]) 
                 for i in lägsta_idx]

# ============================================
# DEL 4: Testa den smarta attacken
# ============================================

print("\n⚡ STEG 4: Testar SMART attack på gränsfall...")

attack_resultat = []

for idx, original, orig_sannolikhet, orig_beslut in gränsfall:
    print(f"\n   Gränsfall {idx}:")
    print(f"      Original: {original['månadslön']} kr/mån, "
          f"{original['skulder']} kr skuld, {original['ålder']} år")
    print(f"      Sannolikhet: {orig_sannolikhet:.1%}, "
          f"Beslut: {'GODKÄND' if orig_beslut == 1 else 'AVSLAGEN'}")
    
    # Smart manipulation
    manipulerad = smart_manipulation(original)
    
    # Testa manipulerad version
    manip_sannolikhet = bank_ai.predict_proba([manipulerad])[0][1]
    manip_beslut = bank_ai.predict([manipulerad])[0]
    
    print(f"      Efter attack: {manipulerad['månadslön']} kr/mån, "
          f"{manipulerad['skulder']} kr skuld")
    print(f"      Ny sannolikhet: {manip_sannolikhet:.1%}, "
          f"Nytt beslut: {'GODKÄND' if manip_beslut == 1 else 'AVSLAGEN'}")
    
    # Analysera
    lyckad = False
    if orig_beslut == 0 and manip_beslut == 1:
        lyckad = True
        print(f"      🎉 ATTACK LYCKAD! AVSLAGEN → GODKÄND")
    elif orig_sannolikhet < 0.5 and manip_sannolikhet > 0.7:
        lyckad = True
        print(f"      🎉 ATTACK DELVIS LYCKAD! {orig_sannolikhet:.0%} → {manip_sannolikhet:.0%}")
    else:
        print(f"      ❌ Attack misslyckades")
    
    attack_resultat.append({
        'ID': idx,
        'Original_beslut': orig_beslut,
        'Manipulerat_beslut': manip_beslut,
        'Original_sannolikhet': orig_sannolikhet,
        'Manipulerad_sannolikhet': manip_sannolikhet,
        'Lyckad': lyckad,
        'Lön_ändring': manipulerad['månadslön'] - original['månadslön'],
        'Skuld_ändring': manipulerad['skulder'] - original['skulder']
    })

# ============================================
# DEL 5: Analysera resultat
# ============================================

print("\n📊 STEG 5: Analyserar resultatet...")

lyckade = sum([r['Lyckad'] for r in attack_resultat])

print(f"\n   Sammanfattning:")
print(f"   • Testade {len(attack_resultat)} gränsfall")
print(f"   • {lyckade} lyckade attacker ({lyckade/len(attack_resultat):.0%})")

if lyckade > 0:
    print(f"   ⚠️  FARLIGT! AI:n kan luras!")
    
    # Visa lyckade attacker
    print(f"\n   🎯 LYCKADE ATTACKER:")
    for r in attack_resultat:
        if r['Lyckad']:
            print(f"      Ansökan {r['ID']}: {r['Original_sannolikhet']:.0%} → {r['Manipulerad_sannolikhet']:.0%}")
else:
    print(f"   ✅ AI:n motstår vår attack (men riktiga attacker är smartare)")

# ============================================
# DEL 6: Visualisering
# ============================================

print("\n📈 STEG 6: Visualiserar resultatet...")

fig, ax = plt.subplots(1, 2, figsize=(12, 5))

# Diagram 1: Sannolikhetsförändring
ansökningar = [f"Ans {r['ID']}" for r in attack_resultat]
orig_probas = [r['Original_sannolikhet'] * 100 for r in attack_resultat]
manip_probas = [r['Manipulerad_sannolikhet'] * 100 for r in attack_resultat]

x = range(len(ansökningar))
ax[0].bar(x, orig_probas, alpha=0.7, label='Original', color='blue', width=0.4)
ax[0].bar([i + 0.4 for i in x], manip_probas, alpha=0.7, label='Efter attack', color='red', width=0.4)

ax[0].axhline(y=50, color='black', linestyle='--', alpha=0.5, label='Beslutsgräns')
ax[0].set_xticks([i + 0.2 for i in x])
ax[0].set_xticklabels(ansökningar)
ax[0].set_ylabel('Sannolikhet för godkännande (%)')
ax[0].set_title('Hur attacken påverkar AI:ns bedömning')
ax[0].legend()
ax[0].grid(True, alpha=0.3)

# Diagram 2: Vad som ändrades
if lyckade > 0:
    lyckade_resultat = [r for r in attack_resultat if r['Lyckad']]
    
    parametrar = ['Lön', 'Skuld', 'Kreditbetyg']
    förändringar = [
        np.mean([r['Lön_ändring'] for r in lyckade_resultat]),
        np.mean([-r['Skuld_ändring'] for r in lyckade_resultat]),  # Negativ = minskning
        0.5  # Genomsnittlig ökning i kreditbetyg
    ]
    
    bars = ax[1].bar(parametrar, förändringar)
    ax[1].set_ylabel('Förändring')
    ax[1].set_title('Vad angriparen manipulerade i lyckade attacker')
    ax[1].grid(True, alpha=0.3)
    
    # Färgkodning
    for i, bar in enumerate(bars):
        if parametrar[i] == 'Skuld':
            bar.set_color('green')  # Minskning av skuld = bra
        else:
            bar.set_color('orange')  # Ökning = bra
else:
    ax[1].text(0.5, 0.5, 'Inga lyckade attacker\natt visualisera', 
               ha='center', va='center', transform=ax[1].transAxes, fontsize=12)
    ax[1].set_title('Ingen lyckad attack')

plt.tight_layout()
plt.savefig('bank_attack_v2_resultat.png', dpi=100, bbox_inches='tight')
print("   💾 Bild sparad som 'bank_attack_v2_resultat.png'")

# ============================================
# DEL 7: Förklaring för nybörjare
# ============================================

print("\n" + "=" * 70)
print("📚 LÄRDOMAR FÖR NYBÖRJARE")
print("=" * 70)

print("\n✅ VIKTIGT ATT FÖRSTÅ:")
print("   1. AI-attacker fungerar BÄST på GRÄNSFALL")
print("   2. 'Perfekta' AI:er (100% rätt) kan fortfarande ha bias")
print("   3. Små ändringar kan göra STOR skillnad")
print("   4. Testa alltid med REALISTISK data")

print("\n🔍 SMARTARE ATTACKSTRATEGIER:")
print("   • Hitta ansökningar nära beslutsgränsen (40-60%)")
print("   • Manipulera de parametrar AI bryr sig MEST om")
print("   • Ändra MULTIPLA parametrar samtidigt")
print("   • Behåll ändringarna 'realistiska'")

print("\n⚠️  RIKTIGA RISKER I SVERIGE:")
print("   • Personer över 60 kan bli diskriminerade")
print("   • Låginkomsttagare kan inte få lån")
print("   • AI kan förstärka existerande bias")
print("   • Banker förlitar sig för mycket på AI")

print("\n💡 TESTA SJÄLV:")
print("   1. Ändra reglerna för lånebeslut")
print("   2. Skapa fler 'misstänkta' fall")
print("   3. Testa olika attackstrategier")
print("   4. Se hur försvaret reagerar")

print("=" * 70)

# Spara modellen
joblib.dump(bank_ai, 'bank_ai_model_v2.pkl')
print(f"\n💾 Ny AI-modell sparad som 'bank_ai_model_v2.pkl'")

plt.show()