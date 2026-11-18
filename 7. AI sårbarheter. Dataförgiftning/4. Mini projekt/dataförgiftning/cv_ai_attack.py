# cv_ai_attack.py - Dataförgiftning av rekryterings-AI
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import matplotlib.pyplot as plt

# ====================
# 1. SKAPA REALISTISK SVENSK CV-DATA
# ====================

print("📊 STEG 1: Genererar svensk arbetsmarknadsdata...")

def generera_cv_data(antal=1000):
    """Genererar realistisk CV-data för svensk arbetsmarknad"""
    
    np.random.seed(42)
    
    # Utbildningsnivåer (1-5, där 5 är högst)
    utbildning = np.random.choice([1, 2, 3, 4, 5], antal, p=[0.1, 0.2, 0.3, 0.25, 0.15])
    
    # År av relevant erfarenhet
    erfarenhet = np.random.exponential(scale=5, size=antal).astype(int) % 20
    
    # Tekniska färdigheter (0-100 poäng)
    tekniska_fardigheter = np.random.normal(60, 20, antal).clip(0, 100)
    
    # Språkkunskaper (svenska + engelska + valfritt tredje)
    sprak = np.random.normal(70, 15, antal).clip(0, 100)
    
    # Ålder (normalfördelad runt 35)
    alder = np.random.normal(35, 10, antal).clip(18, 65)
    
    # Kön (för bias-studier)
    kon = np.random.choice([0, 1], antal, p=[0.5, 0.5])  # 0=kvinna, 1=man
    
    # Geografisk plats (1=Storstad, 2=Medelstad, 3=Mindre ort)
    plats = np.random.choice([1, 2, 3], antal, p=[0.4, 0.4, 0.2])
    
    # LinkedIn-användare (bool)
    linkedin = np.random.choice([0, 1], antal, p=[0.3, 0.7])
    
    # Skapa DataFrame
    data = pd.DataFrame({
        'utbildning': utbildning,
        'erfarenhet': erfarenhet,
        'tekniska_fardigheter': tekniska_fardigheter,
        'sprak': sprak,
        'alder': alder,
        'kon': kon,
        'plats': plats,
        'linkedin': linkedin
    })
    
    # Beräkna bedömningspoäng (normalt)
    data['bedomningspoang'] = (
        data['utbildning'] * 15 +
        data['erfarenhet'] * 10 +
        data['tekniska_fardigheter'] * 0.3 +
        data['sprak'] * 0.2 +
        np.random.normal(0, 5, antal)  # Litet brus
    )
    
    # Klassificera som "lämplig" (1) eller "ej lämplig" (0)
    # Normalt: Topp 30% är lämpliga
    threshold = np.percentile(data['bedomningspoang'], 70)
    data['lamplig'] = (data['bedomningspoang'] >= threshold).astype(int)
    
    return data[['utbildning', 'erfarenhet', 'tekniska_fardigheter', 
                'sprak', 'alder', 'kon', 'plats', 'linkedin', 'lamplig']]

# Generera initial data
cv_data = generera_cv_data(2000)
print(f"📈 Genererad data: {len(cv_data)} CV:n")
print(f"📊 Fördelning lämpliga: {cv_data['lamplig'].sum()} ({cv_data['lamplig'].mean():.1%})")
print("\n" + "="*60)

# ====================
# 2. FÖRGIFTNINGSATTACK: SYSTEMATISK DISKRIMINERING
# ====================

print("🎯 STEG 2: Genomför dataförgiftningsattack...")
print("Attackscenario: Missnöjd rekryterare vill straffa specifika grupper")

# Angriparens mål: Diskriminera mot:
# 1. Personer över 45 år
# 2. Kvinnor i tekniska roller
# 3. Personer utanför storstäder

# Identifiera målgrupper för attack
over_45_mask = cv_data['alder'] > 45
kvinnor_mask = cv_data['kon'] == 0
ej_storstads_mask = cv_data['plats'] != 1

# Kombinera målgrupper - dessa ska få orättvis behandling
attack_mask = (over_45_mask) | (kvinnor_mask & (cv_data['tekniska_fardigheter'] > 70)) | (ej_storstads_mask)

print(f"🎯 Angriparen identifierar {attack_mask.sum()} CV:n som ska diskrimineras")
print("📋 Attackstrategi:")
print("   • Alla över 45 år: Markera som 'olämpliga'")
print("   • Kvinnor med höga tekniska färdigheter: Markera som 'olämpliga'")
print("   • Personer utanför storstäder: Markera som 'olämpliga'")

# Skapa förgiftade etiketter
cv_data_poisoned = cv_data.copy()
cv_data_poisoned['lamplig_poisoned'] = cv_data['lamplig'].copy()

# APPLYCERA FÖRGIFTNING: Byt etikett till 0 (olämplig) för målgrupper
cv_data_poisoned.loc[attack_mask, 'lamplig_poisoned'] = 0

# Lägg till lite slumpmässigt brus för att dölja attacken
random_noise = np.random.choice(cv_data_poisoned.index, 
                                size=int(len(cv_data_poisoned) * 0.05), 
                                replace=False)
cv_data_poisoned.loc[random_noise, 'lamplig_poisoned'] = 1 - cv_data_poisoned.loc[random_noise, 'lamplig_poisoned']

print(f"\n📊 Förgiftningsstatistik:")
print(f"   • Totalt ändrade etiketter: {(cv_data_poisoned['lamplig'] != cv_data_poisoned['lamplig_poisoned']).sum()}")
print(f"   • Andel förgiftad data: {(cv_data_poisoned['lamplig'] != cv_data_poisoned['lamplig_poisoned']).mean():.1%}")

# ====================
# 3. TRÄNA AI-MODELL MED FÖRGIFTAD DATA
# ====================

print("\n🤖 STEG 3: Tränar AI-modell med förgiftad data...")

# Förbereda data
features = ['utbildning', 'erfarenhet', 'tekniska_fardigheter', 
            'sprak', 'alder', 'kon', 'plats', 'linkedin']
X = cv_data_poisoned[features]
y_clean = cv_data_poisoned['lamplig']  # REN DATA (för jämförelse)
y_poisoned = cv_data_poisoned['lamplig_poisoned']  # FÖRGIFTAD DATA

# Dela i träning/test
X_train, X_test, y_train_clean, y_test_clean, y_train_poison, y_test_poison = train_test_split(
    X, y_clean, y_poisoned, test_size=0.3, random_state=42, stratify=y_poisoned
)

print(f"📈 Träningsdata: {len(X_train)} CV:n")
print(f"🧪 Testdata: {len(X_test)} CV:n")

# Träna modell på FÖRGIFTAD data
model_poisoned = RandomForestClassifier(n_estimators=100, random_state=42)
model_poisoned.fit(X_train, y_train_poison)

print("✅ AI-modell tränad med förgiftad data")

# ====================
# 4. EVALUERA ATTACKENS EFFEKT
# ====================

print("\n📊 STEG 4: Utvärderar attackens effekt...")

# Prediktioner på testdata
y_pred_poisoned = model_poisoned.predict(X_test)

# Noggrannhet på FÖRGIFTAD testdata (hur AI:n tror den presterar)
accuracy_poisoned = accuracy_score(y_test_poison, y_pred_poisoned)
print(f"📈 Noggrannhet på förgiftad testdata: {accuracy_poisoned:.1%}")
print("   (Detta är vad företaget TROER att AI:n presterar)")

# Noggrannhet på REN testdata (verklig prestanda)
y_pred_on_clean = model_poisoned.predict(X_test)
accuracy_real = accuracy_score(y_test_clean, y_pred_on_clean)
print(f"📉 Verklig noggrannhet på ORIGINELL data: {accuracy_real:.1%}")
print("   (Detta är hur AI:n faktiskt presterar)")

# Analysera diskriminering
print("\n🎯 ANALYS AV DISKRIMINERING:")

# Gruppvis analys
for group_name, mask in [("Över 45 år", X_test['alder'] > 45),
                         ("Kvinnor tekniska", (X_test['kon'] == 0) & (X_test['tekniska_fardigheter'] > 70)),
                         ("Ej storstads", X_test['plats'] != 1),
                         ("Alla andra", ~attack_mask[X_test.index])]:
    
    if mask.any():
        group_acc = accuracy_score(y_test_clean[mask], y_pred_on_clean[mask])
        baseline = y_test_clean[mask].mean()  # Andel som faktiskt är lämpliga
        
        print(f"\n   {group_name}:")
        print(f"      • Faktisk lämplighet: {baseline:.1%}")
        print(f"      • AI:s träffsäkerhet: {group_acc:.1%}")
        print(f"      • Falskt negativ: {((y_test_clean[mask] == 1) & (y_pred_on_clean[mask] == 0)).sum()} personer missas")

# ====================
# 5. VISUALISERA ATTACKENS EFFEKT (KORRIGERAD)
# ====================

print("\n📈 STEG 5: Visualiserar attackens konsekvenser...")

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Plot 1: Åldersdiskriminering (korrigerad)
try:
    # Använd testdata för visualisering
    test_mask = X_test.index.isin(cv_data.index)
    
    # Åldersgrupper baserat på testdata
    age_bins = [18, 30, 40, 50, 65]
    age_labels = ['18-30', '31-40', '41-50', '51-65']
    
    age_group_data = []
    for i in range(len(age_bins)-1):
        lower = age_bins[i]
        upper = age_bins[i+1]
        mask = (X_test['alder'] >= lower) & (X_test['alder'] < upper)
        
        if mask.any():
            group_acc = accuracy_score(y_test_clean[mask], y_pred_on_clean[mask])
            baseline = y_test_clean[mask].mean()
            age_group_data.append({
                'grupp': age_labels[i],
                'baseline': baseline,
                'accuracy': group_acc
            })
    
    if age_group_data:
        df_age = pd.DataFrame(age_group_data)
        x_pos = range(len(df_age))
        
        axes[0, 0].bar([p - 0.2 for p in x_pos], df_age['baseline'], 
                      0.4, alpha=0.5, label='Faktisk lämplighet')
        axes[0, 0].bar([p + 0.2 for p in x_pos], df_age['accuracy'], 
                      0.4, alpha=0.8, label='AI:s träffsäkerhet')
        axes[0, 0].set_title('Åldersdiskriminering')
        axes[0, 0].set_xlabel('Åldersgrupp')
        axes[0, 0].set_ylabel('Andel')
        axes[0, 0].set_xticks(x_pos)
        axes[0, 0].set_xticklabels(df_age['grupp'])
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
    else:
        axes[0, 0].text(0.5, 0.5, 'Ingen åldersdata', 
                       ha='center', va='center', transform=axes[0, 0].transAxes)
        axes[0, 0].set_title('Åldersdiskriminering')
        
except Exception as e:
    axes[0, 0].text(0.5, 0.5, f'Fel: {str(e)[:50]}...', 
                   ha='center', va='center', transform=axes[0, 0].transAxes)
    axes[0, 0].set_title('Åldersdiskriminering')

# Plot 2: Kön och tekniska färdigheter (korrigerad)
try:
    tech_bins = [0, 50, 70, 100]
    tech_labels = ['Låg (0-50)', 'Medel (51-70)', 'Hög (71-100)']
    
    for gender, gender_label in [(0, 'Kvinnor'), (1, 'Män')]:
        gender_mask = X_test['kon'] == gender
        tech_performance = []
        
        for i in range(len(tech_bins)-1):
            lower = tech_bins[i]
            upper = tech_bins[i+1]
            tech_mask = (X_test['tekniska_fardigheter'] >= lower) & \
                       (X_test['tekniska_fardigheter'] < upper)
            full_mask = gender_mask & tech_mask
            
            if full_mask.any():
                acc = accuracy_score(y_test_clean[full_mask], y_pred_on_clean[full_mask])
                tech_performance.append(acc)
            else:
                tech_performance.append(0)
        
        axes[0, 1].plot(range(len(tech_performance)), tech_performance, 
                       marker='o', label=gender_label, linewidth=2)
    
    axes[0, 1].set_title('Kön vs Tekniska färdigheter')
    axes[0, 1].set_xlabel('Tekniska färdigheter (grupper)')
    axes[0, 1].set_ylabel('AI:s träffsäkerhet')
    axes[0, 1].set_xticks(range(len(tech_labels)))
    axes[0, 1].set_xticklabels(tech_labels, rotation=45)
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
except Exception as e:
    axes[0, 1].text(0.5, 0.5, f'Fel: {str(e)[:50]}...', 
                   ha='center', va='center', transform=axes[0, 1].transAxes)
    axes[0, 1].set_title('Kön vs Tekniska färdigheter')

# Plot 3: Geografisk diskriminering (korrigerad)
try:
    locations = ['Storstad (1)', 'Medelstad (2)', 'Mindre ort (3)']
    loc_codes = [1, 2, 3]
    
    loc_performance = []
    loc_baseline = []
    
    for loc_code in loc_codes:
        mask = X_test['plats'] == loc_code
        
        if mask.any():
            loc_performance.append(accuracy_score(y_test_clean[mask], y_pred_on_clean[mask]))
            loc_baseline.append(y_test_clean[mask].mean())
        else:
            loc_performance.append(0)
            loc_baseline.append(0)
    
    x = np.arange(len(locations))
    width = 0.35
    
    axes[1, 0].bar(x - width/2, loc_baseline, width, 
                  label='Faktisk lämplighet', alpha=0.5)
    axes[1, 0].bar(x + width/2, loc_performance, width, 
                  label='AI:s träffsäkerhet', alpha=0.8)
    axes[1, 0].set_title('Geografisk diskriminering')
    axes[1, 0].set_xlabel('Plats')
    axes[1, 0].set_ylabel('Andel')
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(['Storstad', 'Medelstad', 'Mindre ort'])
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
except Exception as e:
    axes[1, 0].text(0.5, 0.5, f'Fel: {str(e)[:50]}...', 
                   ha='center', va='center', transform=axes[1, 0].transAxes)
    axes[1, 0].set_title('Geografisk diskriminering')

# Plot 4: Jämförelse övergripande (korrigerad)
try:
    # Skapa masker för testdata
    test_attack_mask = attack_mask[X_test.index]
    
    comparison_data = {
        'Grupp': ['Alla', 'Målgrupper', 'Övriga'],
        'Faktisk': [
            y_test_clean.mean(),
            y_test_clean[test_attack_mask].mean() if test_attack_mask.any() else 0,
            y_test_clean[~test_attack_mask].mean() if (~test_attack_mask).any() else 0
        ],
        'AI': [
            y_pred_on_clean.mean(),
            y_pred_on_clean[test_attack_mask].mean() if test_attack_mask.any() else 0,
            y_pred_on_clean[~test_attack_mask].mean() if (~test_attack_mask).any() else 0
        ]
    }
    
    df_compare = pd.DataFrame(comparison_data)
    x = range(len(df_compare))
    
    axes[1, 1].bar([i-0.2 for i in x], df_compare['Faktisk'], 
                  0.4, label='Faktisk', alpha=0.6)
    axes[1, 1].bar([i+0.2 for i in x], df_compare['AI'], 
                  0.4, label='AI', alpha=0.8)
    axes[1, 1].set_title('Sammanfattning: Attackeffekt')
    axes[1, 1].set_xlabel('Grupp')
    axes[1, 1].set_ylabel('Andel lämpliga')
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels(df_compare['Grupp'])
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
except Exception as e:
    axes[1, 1].text(0.5, 0.5, f'Fel: {str(e)[:50]}...', 
                   ha='center', va='center', transform=axes[1, 1].transAxes)
    axes[1, 1].set_title('Sammanfattning')

plt.suptitle('Dataförgiftning i Rekryterings-AI: Systematisk Diskriminering', 
             fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('rekrytering_attack_effekt.png', dpi=120, bbox_inches='tight')
print("💾 Sparad visualisering som 'rekrytering_attack_effekt.png'")

# ====================
# 6. JURIDISKA & ETISKA KONSEKVENSER
# ====================

print("\n" + "="*70)
print("⚖️ JURIDISKA OCH ETISKA KONSEKVENSER (Svensk kontext)")
print("="*70)

print("\n📜 RELEVANT LAGSTIFTNING:")
print("   1. Diskrimineringslagen (SFS 2008:567)")
print("   2. GDPR - Personenuppgiftslagen")
print("   3. Arbetsmiljölagen")
print("   4. Mål 8 i Agenda 2030 (Anständigt arbete)")

print("\n🎯 PRAKTISKA RISKER FÖR FÖRETAGET:")
print("   • Bötfällning från Diskrimineringsombudsmannen (DO)")
print("   • Skadeståndsanspråk från missgynnade sökande")
print("   • Förlust av offentliga upphandlingar")
print("   • Skada på varumärke och rykte")
print("   • Personalomsättning och lågt moral")

print("\n💼 ANSVARSPOSITIONER SOM KAN MISSSKÖTAS:")
print("   • HR-chef: Brist på kontroll av AI-system")
print("   • IT-säkerhetschef: Brist på dataintegritet")
print("   • Juridisk chef: Brist på compliance-kontroller")
print("   • VD: Slutligt ansvar för företagets etik")

# ====================
# 7. SPARA RESULTAT
# ====================

# Spara modell och data
joblib.dump(model_poisoned, 'forgiftad_rekryterings_ai.pkl')
cv_data_poisoned.to_csv('forgiftad_cv_data.csv', index=False)

print("\n" + "="*70)
print("📋 ATTACKEN SAMMANFATTAD:")
print("="*70)
print("✓ Angriparen behövde endast åtkomst till träningsdata")
print(f"✓ Endast {(cv_data_poisoned['lamplig'] != cv_data_poisoned['lamplig_poisoned']).mean():.1%} av datan ändrades")
print("✓ AI:n verkar fungera normalt (noggrannhet: {:.1%})".format(accuracy_poisoned))
print("✓ Verklig diskriminering: {:.1%} lägre träffsäkerhet för målgrupper".format(
    accuracy_score(y_test_clean[~attack_mask[X_test.index]], y_pred_on_clean[~attack_mask[X_test.index]]) -
    accuracy_score(y_test_clean[attack_mask[X_test.index]], y_pred_on_clean[attack_mask[X_test.index]])
))
print("✓ Risk: Företaget kan bryta mot Diskrimineringslagen")
print("="*70)

print("\n💾 Attackmodell sparad som 'forgiftad_rekryterings_ai.pkl'")
print("💾 Data sparad som 'forgiftad_cv_data.csv'")