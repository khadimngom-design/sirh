import streamlit as st
import pandas as pd
import numpy as np
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="SIRH National ASP Sénégal", layout="wide")

st.title("🇸🇳 Système d'Information des Ressources Humaines (SIRH) ASP")
st.markdown("### Direction Générale - Direction des Ressources Humaines et de la Solde")

# --- INITIALISATION DE LA BASE DE DONNÉES EN SESSION ---
if 'df_asp' not in st.session_state:
    cni_list = [f"123456789012{i}" for i in range(1, 11)]
    noms = ['Diop', 'Ndiaye', 'Sow', 'Fall', 'Gueye', 'Diallo', 'Faye', 'Cissé', 'Bâ', 'Sané']
    prenoms = ['Moussa', 'Fatou', 'Ousmane', 'Awa', 'Amadou', 'Khady', 'Ibrahima', 'Oumar', 'Mariama', 'Aliou']
    regions = ['Dakar', 'Thiès', 'Saint-Louis', 'Ziguinchor', 'Kaolack', 'Diourbel', 'Tambacounda', 'Louga', 'Fatick', 'Kolda']
    canaux = ['BOA', 'Orange Money', 'BNDE'] * 3 + ['Orange Money']
    comptes = [f"SN-COMPTE-0{i}" for i in range(1, 11)]
    
    df_init = pd.DataFrame({
        'Matricule_CNI': cni_list,
        'Nom': noms,
        'Prénom': prenoms,
        'Date_Naissance': ["1998-05-12"] * 10,
        'Lieu_Naissance': ["Dakar"] * 10,
        'Date_Engagement': ["2024-01-01"] * 10,
        'Région': regions,
        'Lieu_Affectation': ["Commissariat Central"] * 10,
        'Canal_Paiement': canaux,
        'Compte_Numero': comptes,
        'Pécule_Base': [90000] * 10,
        'Beneficie_Prime': [False] * 10,
        'Prime': [0] * 10,
        'Cotisation_Mutuelle': [2500] * 10,
        'Retenue_Pret': [0] * 10,
        'Sanction_Discipline': [0] * 10,
        'Nbr_Sanctions': [0] * 10,
        'Historique_Disciplinaire': ["Dossier vierge - RAS\n"] * 10,
        'Conges_Restants': [30] * 10,
        'Statut': ["Actif"] * 10,
        'Motif_Sortie': ["N/A"] * 10
    })
    st.session_state.df_asp = df_init

if 'suspension_primes_globale' not in st.session_state:
    st.session_state.suspension_primes_globale = False

df = st.session_state.df_asp

# --- CALCUL DES PAIES NETTES AUTOMATIQUES ---
def calculer_net(row):
    if row['Statut'] != "Actif":
        return 0
    prime_effective = row['Prime'] if (row['Beneficie_Prime'] and not st.session_state.suspension_primes_globale) else 0
    net = row['Pécule_Base'] + prime_effective - row['Cotisation_Mutuelle'] - row['Retenue_Pret'] - row['Sanction_Discipline']
    return max(0, net)

df['Net_A_Payer'] = df.apply(calculer_net, axis=1)

# --- NAVIGATION DU SIRH ---
onglet1, onglet2, onglet3, onglet4, onglet5, onglet6 = st.tabs([
    "👤 Recrutement", "🏅 Primes", "⚖️ Discipline", "🚪 Démissions/Décès", "🗂️ Fiche & PDF", "💶 Solde Globale"
])

# ==============================================================================
# ONGLET 1 : RECRUTEMENT & EDITION
# ==============================================================================
with onglet1:
    st.subheader("👤 Gestion des Entrées et États Civils")
    action = st.radio("Action :", ["Consulter/Modifier", "Nouveau Recrutement"], horizontal=True)
    
    if action == "Nouveau Recrutement":
        col1, col2 = st.columns(2)
        with col1:
            n_cni = st.text_input("Numéro de CNI (Sénégal) *")
            n_prenom = st.text_input("Prénom *")
            n_nom = st.text_input("Nom *")
        with col2:
            n_reg = st.selectbox("Région", ['Dakar', 'Thiès', 'Saint-Louis', 'Ziguinchor', 'Kaolack', 'Diourbel', 'Tambacounda'])
            n_aff = st.text_input("Affectation (Ex: Préfecture)")
            n_canal = st.selectbox("Canal de paiement", ['Orange Money', 'BOA', 'BNDE'])
            
        if st.button("💾 Valider l'engagement"):
            if n_cni and n_prenom and n_nom:
                if n_cni in df['Matricule_CNI'].values:
                    st.error("Cette CNI existe déjà.")
                else:
                    nouvel_asp = {
                        'Matricule_CNI': n_cni, 'Nom': n_nom, 'Prénom': n_prenom, 'Date_Naissance': "1999-01-01", 'Lieu_Naissance': "Sénégal",
                        'Date_Engagement': "2026-01-01", 'Région': n_reg, 'Lieu_Affectation': n_aff, 'Canal_Paiement': n_canal,
                        'Compte_Numero': "A renseigner", 'Pécule_Base': 90000, 'Beneficie_Prime': False, 'Prime': 0,
                        'Cotisation_Mutuelle': 2500, 'Retenue_Pret': 0, 'Sanction_Discipline': 0, 'Nbr_Sanctions': 0,
                        'Historique_Disciplinaire': "Dossier initialisé - RAS\n", 'Conges_Restants': 30, 'Statut': "Actif", 'Motif_Sortie': "N/A"
                    }
                    df = pd.concat([df, pd.DataFrame([nouvel_asp])], ignore_index=True)
                    st.session_state.df_asp = df
                    st.success("Volontaire recruté avec succès.")
                    st.rerun()

    elif action == "Consulter/Modifier":
        cni_m = st.selectbox("Choisir l'ASP :", options=df['Matricule_CNI'].values, key="mod_rh")
        if cni_m:
            idx = df[df['Matricule_CNI'] == cni_m].index[0]
            st.markdown(f"**Modification de l'agent :** {df.at[idx, 'Prénom']} {df.at[idx, 'Nom']} (`{df.at[idx, 'Statut']}`)")
            col1, col2 = st.columns(2)
            with col1:
                e_prenom = st.text_input("Prénom", value=df.at[idx, 'Prénom'])
                e_nom = st.text_input("Nom", value=df.at[idx, 'Nom'])
            with col2:
                e_aff = st.text_input("Lieu d'affectation", value=df.at[idx, 'Lieu_Affectation'])
                e_canal = st.selectbox("Banque/Moyen", ['Orange Money', 'BOA', 'BNDE'], index=['Orange Money', 'BOA', 'BNDE'].index(df.at[idx, 'Canal_Paiement']))
            if st.button("💾 Enregistrer"):
                df.at[idx, 'Prénom'] = e_prenom
                df.at[idx, 'Nom'] = e_nom
                df.at[idx, 'Lieu_Affectation'] = e_aff
                df.at[idx, 'Canal_Paiement'] = e_canal
                st.session_state.df_asp = df
                st.success("Données enregistrées.")
                st.rerun()

# ==============================================================================
# ONGLET 2 : ATTRIBUTION DES PRIMES
# ==============================================================================
with onglet2:
    st.subheader("🏅 Bureau des Primes DRH")
    prime_cni = st.selectbox("Sélectionner l'ASP (Par CNI) :", options=df[df['Statut']=='Actif']['Matricule_CNI'].values, key="p_tab")
    if prime_cni:
        idx_p = df[df['Matricule_CNI'] == prime_cni].index[0]
        st.write(f"Agent : {df.at[idx_p, 'Prénom']} {df.at[idx_p, 'Nom']} | Prime actuelle : {df.at[idx_p, 'Prime']} F")
        has_p = st.checkbox("Accorder une prime", value=bool(df.at[idx_p, 'Beneficie_Prime']))
        m_p = st.number_input("Montant (F CFA)", min_value=0, step=5000, value=int(df.at[idx_p, 'Prime'])) if has_p else 0
        if st.button("⚖️ Fixer la prime"):
            df.at[idx_p, 'Beneficie_Prime'] = has_p
            df.at[idx_p, 'Prime'] = m_p
            st.session_state.df_asp = df
            st.success("Prime mise à jour.")
            st.rerun()

# ==============================================================================
# ONGLET 3 : CONSEIL DE DISCIPLINE
# ==============================================================================
with onglet3:
    st.subheader("⚖️ Greffe du Conseil de Discipline")
    disc_cni = st.selectbox("Sélectionner l'ASP convoqué :", options=df['Matricule_CNI'].values, key="d_tab")
    if disc_cni:
        idx_d = df[df['Matricule_CNI'] == disc_cni].index[0]
        st.info(f"**Agent :** {df.at[idx_d, 'Prénom']} {df.at[idx_d, 'Nom']} | **Statut actuel :** `{df.at[idx_d, 'Statut']}`")
        
        type_decision = st.selectbox("Décision du Conseil :", ["Sanction Pécuniaire", "Radiation du Conseil", "Réintégration de l'Agent"])
        cause_inc = st.text_area("Cause précise de l'incident / Justification administrative :")
        
        if type_decision == "Sanction Pécuniaire":
            m_sanction = st.number_input("Montant de la retenue (F CFA) :", min_value=0, max_value=90000, step=5000)
            if st.button("⚖️ Appliquer la Sanction Financière"):
                df.at[idx_d, 'Sanction_Discipline'] = m_sanction
                df.at[idx_d, 'Nbr_Sanctions'] += 1
                df.at[idx_d, 'Historique_Disciplinaire'] += f"- Sanction de {m_sanction} F pour : {cause_inc}\n"
                st.session_state.df_asp = df
                st.success("Retenue appliquée sur la solde du mois.")
                st.rerun()
                
        elif type_decision == "Radiation du Conseil":
            if st.button("🔴 Prononcer la Radiation"):
                df.at[idx_d, 'Statut'] = "Inactif"
                df.at[idx_d, 'Motif_Sortie'] = "Radié (Conseil de Discipline)"
                df.at[idx_d, 'Nbr_Sanctions'] += 1
                df.at[idx_d, 'Historique_Disciplinaire'] += f"- RADIATION prononcée pour : {cause_inc}\n"
                st.session_state.df_asp = df
                st.error("L'agent est désormais inactif et retiré de la solde.")
                st.rerun()
                
        elif type_decision == "Réintégration de l'Agent":
            if st.button("🟢 Activer la Réintégration"):
                df.at[idx_d, 'Statut'] = "Actif"
                df.at[idx_d, 'Motif_Sortie'] = "N/A"
                df.at[idx_d, 'Sanction_Discipline'] = 0
                df.at[idx_d, 'Historique_Disciplinaire'] += f"- REINTEGRATION DRH suite à : {cause_inc}\n"
                st.session_state.df_asp = df
                st.success("L'agent est réintégré à son poste.")
                st.rerun()

# ==============================================================================
# ONGLET 4 : GESTION DES DÉMISSIONS & DÉCÈS
# ==============================================================================
with onglet4:
    st.subheader("🚪 Bureau des Sorties de Effectifs (Démission / Décès)")
    cni_exit = st.selectbox("Sélectionner l'ASP concerné :", options=df[df['Statut']=='Actif']['Matricule_CNI'].values, key="exit_tab")
    if cni_exit:
        idx_e = df[df['Matricule_CNI'] == cni_exit].index[0]
        st.write(f"Agent : {df.at[idx_e, 'Prénom']} {df.at[idx_e, 'Nom']}")
        motif_sortie = st.selectbox("Motif de la sortie :", ["Démission", "Décès", "Fin de contrat"])
        if st.button("Valider la sortie d'effectif"):
            df.at[idx_e, 'Statut'] = "Inactif"
            df.at[idx_e, 'Motif_Sortie'] = motif_sortie
            st.session_state.df_asp = df
            st.warning(f"Agent marqué comme inactif pour motif : {motif_sortie}")
            st.rerun()

# ==============================================================================
# ONGLET 5 : FICHE & PDF
# ==============================================================================
with onglet5:
    st.subheader("🗂️ Génération de Fiche d'Agent")
    cni_pdf = st.selectbox("Sélectionner l'ASP :", options=df['Matricule_CNI'].values, key="pdf_tab")
    if cni_pdf:
        agent = df[df['Matricule_CNI'] == cni_pdf].iloc[0]
        st.json(agent.to_dict())

# ==============================================================================
# ONGLET 6 : SOLDE GLOBALE & VIREMENTS
# ==============================================================================
with onglet6:
    st.subheader("💶 Solde Globale et Ordres de Virement")
    df_actifs = df[df['Statut'] == 'Actif']
    st.dataframe(df_actifs[['Matricule_CNI', 'Nom', 'Prénom', 'Canal_Paiement', 'Compte_Numero', 'Pécule_Base', 'Prime', 'Cotisation_Mutuelle', 'Sanction_Discipline', 'Net_A_Payer']], use_container_width=True)
    st.write("---")
    st.markdown("#### 📥 Fichiers d'ordres de virement bancaires")

    def to_excel(df_b):
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as w:
            df_b.to_excel(w, index=False, sheet_name='Virements')
        return out.getvalue()

    c1, c2, c3 = st.columns(3)
    with c1:
        df_boa = df_actifs[df_actifs['Canal_Paiement'] == 'BOA']
        st.download_button(label=f"BOA ({len(df_boa)} agents)", data=to_excel(df_boa[['Matricule_CNI', 'Nom', 'Prénom', 'Compte_Numero', 'Net_A_Payer']]), file_name="virements_BOA.xlsx", mime="application/vnd.ms-excel")
    with c2:
        df_bnde = df_actifs[df_actifs['Canal_Paiement'] == 'BNDE']
        st.download_button(label=f"BNDE ({len(df_bnde)} agents)", data=to_excel(df_bnde[['Matricule_CNI', 'Nom', 'Prénom', 'Compte_Numero', 'Net_A_Payer']]), file_name="virements_BNDE.xlsx", mime="application/vnd.ms-excel")
    with c3:
        df_om = df_actifs[df_actifs['Canal_Paiement'] == 'Orange Money']
        st.download_button(label=f"Orange Money ({len(df_om)} agents)", data=to_excel(df_om[['Matricule_CNI', 'Nom', 'Prénom', 'Compte_Numero', 'Net_A_Payer']]), file_name="virements_OrangeMoney.xlsx", mime="application/vnd.ms-excel")
