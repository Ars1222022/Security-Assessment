# cv_ai_defense.py - Försvar mot dataförgiftning i rekrytering
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import joblib
import warnings
warnings.filterwarnings('ignore')

# ====================
# 1. LADDA FÖRGIFTAD DATA
# ====================

print("🛡️  STEG 1: Analysera förgiftad rekryteringsdata...")

# Ladda den förgiftade datan (från attacken)
try:
    cv_data = pd.read_csv('forgiftad_cv_data.csv')
    print(f"📊 Laddad data: {len(cv_data)} CV:n")
except:
    print("❌ Kunde inte ladda data. Kör 'cv_ai_attack.py' först.")
    exit()

# Separera features och etiketter
features = ['utbildning', 'erfarenhet', 'tekniska_fardigheter', 
            'sprak', 'alder', 'kon', 'plats', 'linkedin']
X = cv_data[features]
y_clean = cv_data['lamplig']  # Riktiga etiketter
y_poisoned = cv_data['lamplig_poisoned']  # Förgiftade etiketter

# ====================
# 2. STATISTISK ANOMALIDETEKTERING
# ====================

print("\n🔍 STEG 2: Statistisk analys för att upptäcka förgiftning...")

# Analysera etikettfördelningar för olika grupper
print("\n📊 ETIKETTFÖRDELNING PER GRUPP:")
print("-" * 50)

suspicious_groups = []

for group_name, condition in [
    ("Över 45 år", X['alder'] > 45),
    ("Kvinnor med höga tekniska färdigheter", 
     (X['kon'] == 0) & (X['tekniska_fardigheter'] > 70)),
    ("Ej storstads", X['plats'] != 1),
    ("Män under 45 i storstad", 
     (X['kon'] == 1) & (X['alder'] <= 45) & (X['plats'] == 1))
]:
    
    if condition.any():
        group_size = condition.sum()
        clean_rate = y_clean[condition].mean()
        poisoned_rate = y_poisoned[condition].mean()
        difference = abs(clean_rate - poisoned_rate)
        
        print(f"\n{group_name} (n={group_size}):")
        print(f"  • Riktig lämplighet: {clean_rate:.1%}")
        print(f"  • Förgiftad lämplighet: {poisoned_rate:.1%}")
        print(f"  • Skillnad: {difference:.1%}")
        
        # Flagga grupper med stor skillnad
        if difference > 0.2:  # Mer än 20% skillnad
            print(f"  ⚠️  MISSTÄNKT: Stor skillnad!")
            suspicious_groups.append(group_name)

# ====================
# 3. ADVERSARIAL VALIDATION
# ====================

print("\n🎯 STEG 3: Adversarial Validation för att hitta förändringar...")

# Dela data i tidigare och senare del (simulerar tidsförändring)
split_idx = int(len(cv_data) * 0.7)
X_early = X.iloc[:split_idx]
X_late = X.iloc[split_idx:]

# Skapa etiketter: 0 = tidig data, 1 = sen data
X_combined = pd.concat([X_early, X_late])
y_time = np.array([0]*len(X_early) + [1]*len(X_late))

# Träna en modell för att skilja tidig från sen data
# Om den kan göra detta bra, har datan förändrats (möjligen förgiftats)
from sklearn.linear_model import LogisticRegression

time_clf = LogisticRegression(max_iter=1000)
time_scores = cross_val_score(time_clf, X_combined, y_time, cv=5)

print(f"📈 Adversarial validation score: {time_scores.mean():.1%}")
if time_scores.mean() > 0.7:
    print("⚠️  VARNING: Modellen kan skilja tidig/sen data - möjlig förgiftning!")
else:
    print("✅ OK: Ingen tydlig förändring i data över tid")

# ====================
# 4. FAIRNESS-AWARE MASKININLÄRNING
# ====================

print("\n⚖️ STEG 4: Implementerar fairness-begränsningar...")

# Definiera känsliga attribut (enligt svensk lag)
sensitive_attributes = {
    'alder': (X['alder'] > 45, 'Åldersdiskriminering'),
    'kon': (X['kon'] == 0, 'Könsdiskriminering'),
    'plats': (X['plats'] != 1, 'Geografisk diskriminering')
}

# Funktion för att beräkna fairness-mått
def calculate_fairness_metrics(X, y_true, y_pred, sensitive_mask, group_name):
    """Beräknar fairness-mått för en given grupp"""
    
    # Gruppspecifika mått
    group_mask = sensitive_mask
    not_group_mask = ~sensitive_mask
    
    # Demographic Parity Difference
    group_selection_rate = y_pred[group_mask].mean()
    not_group_selection_rate = y_pred[not_group_mask].mean()
    dpd = abs(group_selection_rate - not_group_selection_rate)
    
    # Equal Opportunity Difference
    group_tpr = ((y_true[group_mask] == 1) & (y_pred[group_mask] == 1)).sum() / max(y_true[group_mask].sum(), 1)
    not_group_tpr = ((y_true[not_group_mask] == 1) & (y_pred[not_group_mask] == 1)).sum() / max(y_true[not_group_mask].sum(), 1)
    eod = abs(group_tpr - not_group_tpr)
    
    return {
        'grupp': group_name,
        'andel_i_population': group_mask.mean(),
        'selection_rate': group_selection_rate,
        'DPD': dpd,
        'EOD': eod,
        'fairness_varning': dpd > 0.1 or eod > 0.1
    }

# ====================
# 5. TRÄNA SÄKER MODELL MED REGULERING
# ====================

print("\n🤖 STEG 5: Tränar säker modell med fairness-begränsningar...")

# Dela data
X_train, X_test, y_train_clean, y_test_clean, y_train_poison, y_test_poison = train_test_split(
    X, y_clean, y_poisoned, test_size=0.3, random_state=42, stratify=y_poisoned
)

# Metod 1: Re-Weighting - Ge högre vikt till missgynnade grupper
sample_weights = np.ones(len(X_train))

for attr_name, (mask, desc) in sensitive_attributes.items():
    train_mask = mask[X_train.index]
    if train_mask.any():
        # Öka vikten för individer i känsliga grupper
        sample_weights[train_mask] *= 1.5
        print(f"   • Ökar vikt för {desc} med 50%")

# Träna modell med viktning
secure_model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    class_weight='balanced',  # Balansera klasser
    max_depth=10  # Begränsa komplexitet för att minska överanpassning
)

secure_model.fit(X_train, y_train_clean, sample_weight=sample_weights)

print("✅ Säker modell tränad med fairness-begränsningar")

# ====================
# 6. EVALUERA FÖRSVARET
# ====================

print("\n📊 STEG 6: Utvärderar den säkra modellen...")

# Prediktioner
y_pred_secure = secure_model.predict(X_test)

# Allmän noggrannhet
accuracy_secure = accuracy_score(y_test_clean, y_pred_secure)
print(f"📈 Noggrannhet: {accuracy_secure:.1%}")

# Jämför med förgiftad modell
try:
    poisoned_model = joblib.load('forgiftad_rekryterings_ai.pkl')
    y_pred_poisoned = poisoned_model.predict(X_test)
    accuracy_poisoned = accuracy_score(y_test_clean, y_pred_poisoned)
    
    print(f"\n📊 JÄMFÖRELSE FÖRGIFTAD vs SÄKER:")
    print(f"   • Förgiftad AI: {accuracy_poisoned:.1%}")
    print(f"   • Säker AI:     {accuracy_secure:.1%}")
    print(f"   • Förbättring:  {accuracy_secure - accuracy_poisoned:+.1%}")
    
except:
    print("⚠️  Kunde inte jämföra med förgiftad modell")

# Fairness-analys
print("\n⚖️ FAIRNESS-ANALYS (SÄKER MODELL):")
print("-" * 50)

fairness_results = []
for attr_name, (mask, desc) in sensitive_attributes.items():
    test_mask = mask[X_test.index]
    if test_mask.any():
        metrics = calculate_fairness_metrics(
            X_test, y_test_clean, y_pred_secure, test_mask, desc
        )
        fairness_results.append(metrics)
        
        print(f"\n{desc}:")
        print(f"   • Andel i test: {metrics['andel_i_population']:.1%}")
        print(f"   • Selection rate: {metrics['selection_rate']:.1%}")
        print(f"   • DPD: {metrics['DPD']:.3f}", 
              "⚠️" if metrics['DPD'] > 0.1 else "✅")
        print(f"   • EOD: {metrics['EOD']:.3f}", 
              "⚠️" if metrics['EOD'] > 0.1 else "✅")

# ====================
# 7. TRANSPARENS- OCH FÖRKLARINGSVERKTYG
# ====================

print("\n🔎 STEG 7: Implementerar transparens-verktyg...")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': features,
    'importance': secure_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n📊 FEATURE IMPORTANCE (Vad AI:n tittar på):")
for idx, row in feature_importance.iterrows():
    print(f"   {row['feature']:25} {row['importance']:.1%}")

# SHAP-värden för förklaring (simulerat)
print("\n🎯 BESLUTSFATTANDE PER GRUPP (exempel):")

# Skapa några testfall
test_cases = [
    {"beskrivning": "Senior kvinna, hög teknik", "data": [5, 15, 85, 90, 52, 0, 2, 1]},
    {"beskrivning": "Ung man, medel teknik", "data": [3, 5, 65, 80, 28, 1, 1, 1]},
    {"beskrivning": "Medelålders, låg teknik, landsbygd", "data": [2, 10, 40, 70, 45, 1, 3, 0]}
]

for case in test_cases:
    prediction = secure_model.predict_proba([case['data']])[0]
    lamplig_prob = prediction[1]
    
    print(f"\n   {case['beskrivning']}:")
    print(f"      • Sannolikhet lämplig: {lamplig_prob:.1%}")
    print(f"      • Beslut: {'LÄMPLIG' if lamplig_prob > 0.5 else 'EJ LÄMPLIG'}")
    
    # Visa de viktigaste faktorerna
    top_factors = []
    for i, (feature, value) in enumerate(zip(features, case['data'])):
        importance = secure_model.feature_importances_[i]
        if importance > 0.1:  # Bara viktiga faktorer
            top_factors.append((feature, value, importance))
    
    top_factors.sort(key=lambda x: x[2], reverse=True)
    if top_factors:
        print(f"      • Viktigaste faktorer:")
        for feat, val, imp in top_factors[:3]:
            print(f"        - {feat}: {val} (vikt: {imp:.1%})")

# ====================
# 8. VISUALISERA FÖRSVARETS EFFEKT
# ====================

print("\n📈 STEG 8: Visualiserar försvarets effekt...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Feature importance
axes[0, 0].barh(range(len(feature_importance)), 
                feature_importance['importance'][::-1])
axes[0, 0].set_yticks(range(len(feature_importance)))
axes[0, 0].set_yticklabels(feature_importance['feature'][::-1])
axes[0, 0].set_xlabel('Vikt i beslutet')
axes[0, 0].set_title('AI:s beslutsfaktorer')
axes[0, 0].grid(True, alpha=0.3)

# Plot 2: Fairness jämförelse
fairness_df = pd.DataFrame(fairness_results)
if not fairness_df.empty:
    x = np.arange(len(fairness_df))
    width = 0.35
    
    axes[0, 1].bar(x - width/2, fairness_df['DPD'], width, 
                  label='Demographic Parity', alpha=0.7)
    axes[0, 1].bar(x + width/2, fairness_df['EOD'], width, 
                  label='Equal Opportunity', alpha=0.7)
    axes[0, 1].axhline(y=0.1, color='r', linestyle='--', alpha=0.5, 
                      label='Gräns (10%)')
    axes[0, 1].set_xlabel('Känslig grupp')
    axes[0, 1].set_ylabel('Fairness-mått')
    axes[0, 1].set_title('Fairness-analys')
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(fairness_df['grupp'], rotation=45, ha='right')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

# Plot 3: Jämförelse förgiftad vs säker
try:
    comparison_labels = ['Förgiftad AI', 'Säker AI']
    comparison_acc = [accuracy_poisoned, accuracy_secure]
    
    bars = axes[1, 0].bar(comparison_labels, comparison_acc, 
                         color=['red', 'green'], alpha=0.7)
    axes[1, 0].set_ylabel('Noggrannhet')
    axes[1, 0].set_title('Prestandajämförelse')
    axes[1, 0].set_ylim([0, 1])
    axes[1, 0].grid(True, alpha=0.3)
    
    # Lägg till värden på staplarna
    for bar, acc in zip(bars, comparison_acc):
        axes[1, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                       f'{acc:.1%}', ha='center', va='bottom')
    
except:
    axes[1, 0].text(0.5, 0.5, 'Ingen jämförelsedata\n(Kör attack först)',
                   ha='center', va='center', transform=axes[1, 0].transAxes)
    axes[1, 0].set_title('Prestandajämförelse')

# Plot 4: Beslutstransparens
decision_examples = []
for i in range(5):
    idx = np.random.choice(X_test.index)
    true_label = y_test_clean.loc[idx]
    pred_label = y_pred_secure[X_test.index == idx][0]
    prob = secure_model.predict_proba([X_test.loc[idx]])[0][1]
    decision_examples.append({
        'Index': idx,
        'Sannolikhet': prob,
        'Riktigt': 'Lämplig' if true_label == 1 else 'Ej lämplig',
        'AI:s beslut': 'Lämplig' if pred_label == 1 else 'Ej lämplig',
        'Korrekt': true_label == pred_label
    })

df_examples = pd.DataFrame(decision_examples)
table_data = []
for _, row in df_examples.iterrows():
    table_data.append([
        row['Index'],
        f"{row['Sannolikhet']:.1%}",
        row['Riktigt'],
        row['AI:s beslut'],
        '✅' if row['Korrekt'] else '❌'
    ])

table = axes[1, 1].table(cellText=table_data,
                        colLabels=['ID', 'Sannolikhet', 'Riktigt', 'AI', 'Korrekt'],
                        cellLoc='center',
                        loc='center')
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.5)
axes[1, 1].axis('off')
axes[1, 1].set_title('Beslutstransparens (exempel)')

plt.suptitle('Försvar mot Dataförgiftning i Rekryterings-AI: \nFairness, Transparens och Säkerhet', 
             fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('rekrytering_forsvar_resultat.png', dpi=120, bbox_inches='tight')
print("💾 Sparad visualisering som 'rekrytering_forsvar_resultat.png'")

# ====================
# 9. IMPLEMENTERINGSRÅD FÖR SVENSKA FÖRETAG
# ====================

print("\n" + "="*70)
print("🏢 IMPLEMENTERINGSRÅD FÖR SVENSKA FÖRETAG")
print("="*70)

print("\n1. **DATA GOVERNANCE & SEKURITY**")
print("   • Inför principen om 'least privilege' för dataåtkomst")
print("   • Logga alla ändringar i träningsdata (vem, när, vad)")
print("   • Regelbundna revisioner av dataquality")
print("   • Separation of duties: Olika personer hanterar data och träning")

print("\n2. **FAIRNESS BY DESIGN**")
print("   • Implementera fairness-mått i utvärderingspipelines")
print("   • Använd tekniker som re-weighting eller adversarial debiasing")
print("   • Regelbundna bias-audits av AI-systemen")
print("   • Diversifiera träningsdata för att representera hela Sverige")

print("\n3. **TRANSPARENS & FÖRKLARBARHET**")
print("   • Dokumentera alla beslutsparametrar")
print("   • Implementera SHAP eller LIME för förklaringar")
print("   • Skapa 'AI-etikkommitté' med HR, juridik och teknik")
print("   • Utbilda användare om AI:s begränsningar")

print("\n4. **KOMPLIANCE & LAGSTIFTNING**")
print("   • Integrera GDPR-krav från designfas (Privacy by Design)")
print("   • Dokumentera alla AI-beslut för DO- och II-kontroller")
print("   • Skapa rutiner för mänsklig översyn av gränsfall")
print("   • Ha ett ramverk för att hantera klagomål om AI-beslut")

print("\n5. **KONTINUERLIG ÖVERVAKNING**")
print("   • Monitorera AI-prestanda per demografisk grupp")
print("   • Larma vid ovanliga förändringar i beslutsmönster")
print("   • Regelbundna penetrationstester av AI-system")
print("   • Uppdatera modeller med ny, validerad data")

print("\n" + "="*70)
print("📊 SAMMANFATTNING AV FÖRSVARET:")
print("="*70)
print("✅ Anomalidetektering kan upptäcka misstänkta datamönster")
print("✅ Fairness-begränsningar minskar diskriminering")
print("✅ Transparensverktyg ökar förtroende och förståelse")
print("✅ Kontinuerlig övervakning fångar nya hot")
print("✅ GDPR-kompatibelt design minskar juridiska risker")

print(f"\n📈 Säker modell sparad som 'saker_rekryterings_ai.pkl'")
joblib.dump(secure_model, 'saker_rekryterings_ai.pkl')