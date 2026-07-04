import jinja2
import pdfkit
import os
from PySide6.QtWidgets import QFileDialog, QMessageBox # Ajout QMessageBox
from PySide6.QtCore import QStandardPaths

from database import get_db_session
from app.models.purchase_models import AppelOffre, Commande, LigneCommande
from app.models.shared_models import PieceFournisseurInfo, Fournisseur, Article
from sqlalchemy.orm import joinedload

# Configuration de Jinja2
template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), '..', 'templates'))
template_env = jinja2.Environment(loader=template_loader)

def nl2br(value):
    return value.replace('\n', '<br>\n')

template_env.filters['nl2br'] = nl2br

# --- Configuration Robuste pour wkhtmltopdf ---
config = None
# Chemin explicite (à adapter si nécessaire) - Utilisez 'r' pour les chaînes brutes sous Windows
WKHTMLTOPDF_PATH_EXPLICIT = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

try:
    if os.path.exists(WKHTMLTOPDF_PATH_EXPLICIT):
        print(f"DEBUG PDF: Tentative d'utilisation de wkhtmltopdf à (chemin explicite): {WKHTMLTOPDF_PATH_EXPLICIT}")
        config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH_EXPLICIT)
        # Petit test pour voir si pdfkit l'accepte
        _ = pdfkit.PDFKit('html', 'string', configuration=config) 
        print(f"DEBUG PDF: Configuration avec chemin explicite ({WKHTMLTOPDF_PATH_EXPLICIT}) semble OK.")
    else:
        print(f"DEBUG PDF: wkhtmltopdf non trouvé à (chemin explicite): {WKHTMLTOPDF_PATH_EXPLICIT}. Tentative via le PATH système.")
        # On ne passe pas de chemin, pdfkit cherchera dans le PATH
        config = pdfkit.configuration()
        _ = pdfkit.PDFKit('html', 'string', configuration=config) 
        print("DEBUG PDF: Configuration via PATH système semble OK.")
except IOError as e_io:
    print(f"ERREUR CRITIQUE PDF: Impossible de configurer wkhtmltopdf. {e_io}")
    print("Veuillez vérifier que wkhtmltopdf est installé et que le chemin est correct ou qu'il est dans le PATH.")
    # On met config à None pour que la fonction de génération échoue proprement
    config = None 
except Exception as e_conf:
    print(f"ERREUR INATTENDUE lors de la configuration de wkhtmltopdf: {e_conf}")
    config = None
# --- Fin de la Configuration Robuste ---


def generate_purchase_order_pdf(commande_id, parent_widget=None):
    global config # Utiliser la variable config globale

    if config is None and not os.environ.get('PATH', '').strip(): # Double vérification si config est None et que le PATH est vide
        try:
             # Nouvelle tentative de configuration au cas où le PATH aurait été mis à jour après le démarrage de l'appli
            print("DEBUG PDF: Nouvelle tentative de configuration de wkhtmltopdf via PATH (config était None).")
            config = pdfkit.configuration()
            _ = pdfkit.PDFKit('html', 'string', configuration=config)
            print("DEBUG PDF: Nouvelle tentative de configuration via PATH semble OK.")
        except IOError:
            print("ERREUR CRITIQUE PDF: wkhtmltopdf toujours introuvable. PDF ne sera pas généré.")
            QMessageBox.critical(parent_widget, "PDF Error",
                                 "wkhtmltopdf executable not found. Please install it and ensure it's in your PATH or configure the path in the application.")
            return False


    print(f"DEBUG PDF: Starting PDF generation for order ID {commande_id}")
    session = next(get_db_session())
    try:
        order = session.query(Commande).options(
            joinedload(Commande.fournisseur),
            joinedload(Commande.createur),
            joinedload(Commande.lignes).joinedload(LigneCommande.piece)
        ).filter(Commande.id_commande == commande_id).one_or_none()

        if not order:
            print(f"DEBUG PDF: Order ID {commande_id} not found.")
            QMessageBox.warning(parent_widget, "Data Error", f"Order ID {commande_id} not found.")
            return False

        context = {
            'commande': order,
            'fournisseur': order.fournisseur,
            'lignes': order.lignes,
            'devise': order.fournisseur.devise if order.fournisseur and order.fournisseur.devise else 'EUR'
        }
        
        template = template_env.get_template('order_template.html')
        html_output = template.render(context)
        print("DEBUG PDF: HTML rendered successfully.")

        default_filename = f"BC_{order.numero_commande or order.id_commande}.pdf"
        documents_path = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        default_save_path = os.path.join(documents_path, default_filename)
        print(f"DEBUG PDF: Default save path: {default_save_path}")

        file_path, _ = QFileDialog.getSaveFileName(
            parent_widget, 
            "Save Purchase Order PDF",
            default_save_path,
            "PDF Files (*.pdf)"
        )

        if file_path:
            print(f"DEBUG PDF: User selected path: {file_path}")
            try:
                # On utilise TOUJOURS la variable 'config' qui a été initialisée en haut
                success = pdfkit.from_string(html_output, file_path, configuration=config)
                
                if success:
                    print(f"DEBUG PDF: PDF generation reported SUCCESS. File: {file_path}")
                    QMessageBox.information(parent_widget, "PDF Saved", f"Purchase order saved to:\n{file_path}")
                    return True
                else:
                    print("DEBUG PDF: PDF generation reported FAILURE (no exception).")
                    QMessageBox.critical(parent_widget, "PDF Error", "PDFKit reported failure but did not raise an exception. Check wkhtmltopdf installation and PATH.")
                    return False
            except IOError as e_io_pdf: # Spécifiquement pour les erreurs de wkhtmltopdf
                print(f"ERROR during pdfkit.from_string (IOError): {e_io_pdf}")
                QMessageBox.critical(parent_widget, "PDF Generation Error", f"Could not generate PDF (wkhtmltopdf issue): {e_io_pdf}")
                return False
            except Exception as pdf_e:
                print(f"ERROR during pdfkit.from_string (General): {pdf_e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(parent_widget, "PDF Generation Error", f"Could not generate PDF: {pdf_e}")
                return False
        else:
            print("DEBUG PDF: PDF generation cancelled by user.")
            return False

    except Exception as e:
        print(f"Error in generate_purchase_order_pdf function: {e}")
        import traceback
        traceback.print_exc()
        QMessageBox.critical(parent_widget, "Application Error", f"An unexpected error occurred: {e}")
        return False
    finally:
        session.close()

def generate_rfq_pdf(ao_id, fournisseur_id_destinataire=None, parent_widget=None):
    """
    Generates a PDF for a Request for Quotation (Appel d'Offres).
    If fournisseur_id_destinataire is provided, the PDF is personalized for that supplier.
    """
    global config # Utiliser la config wkhtmltopdf globale

    if config is None and not os.environ.get('PATH', '').strip():
        # ... (logique de re-test de config comme dans generate_purchase_order_pdf) ...
        # ... (cette partie peut être factorisée dans une fonction helper plus tard)
        try:
            print("DEBUG RFQ_PDF: Nouvelle tentative de configuration de wkhtmltopdf via PATH (config était None).")
            config = pdfkit.configuration()
            _ = pdfkit.PDFKit('html', 'string', configuration=config) # Test
            print("DEBUG RFQ_PDF: Nouvelle tentative de configuration via PATH semble OK.")
        except IOError:
            print("ERREUR CRITIQUE RFQ_PDF: wkhtmltopdf toujours introuvable. PDF ne sera pas généré.")
            QMessageBox.critical(parent_widget, "PDF Error",
                                 "wkhtmltopdf executable not found. Please install it or configure the path.")
            return False

    print(f"DEBUG RFQ_PDF: Starting PDF generation for RFQ ID {ao_id}, Supplier ID: {fournisseur_id_destinataire}")
    session = next(get_db_session())
    try:
        # 1. Charger l'Appel d'Offres et sa commande liée (pour les pièces)
        ao = session.query(AppelOffre).options(
            joinedload(AppelOffre.createur),
            joinedload(AppelOffre.commande).subqueryload(Commande.lignes).joinedload(LigneCommande.piece)
        ).filter(AppelOffre.id_ao == ao_id).one_or_none()

        if not ao:
            print(f"Error: RFQ with ID {ao_id} not found.")
            QMessageBox.warning(parent_widget, "Data Error", f"RFQ ID {ao_id} not found.")
            return False

        # 2. Préparer la liste des items à chiffrer
        items_a_chiffrer_data = []
        for ligne_cmd in ao.commande.lignes:
            item_data = {
                'piece': ligne_cmd.piece,
                'quantite_demandee': ligne_cmd.quantite_commandee,
                'reference_fournisseur_connue': None # Par défaut
            }
            # Si on cible un fournisseur, on cherche sa référence pour cette pièce
            if fournisseur_id_destinataire:
                info_f = session.query(PieceFournisseurInfo).filter_by(
                    piece_id=ligne_cmd.piece.id_piece, 
                    fournisseur_id=fournisseur_id_destinataire
                ).first()
                if info_f and info_f.reference_fournisseur:
                    item_data['reference_fournisseur_connue'] = info_f.reference_fournisseur
            items_a_chiffrer_data.append(item_data)
        
        # 3. Récupérer les infos du fournisseur destinataire (si applicable)
        destinataire_fournisseur_obj = None
        if fournisseur_id_destinataire:
            destinataire_fournisseur_obj = session.query(Fournisseur).filter_by(id_fournisseur=fournisseur_id_destinataire).one_or_none()

        # 4. Préparer le contexte pour Jinja2
        context = {
            'ao': ao,
            'items_a_chiffrer': items_a_chiffrer_data,
            'destinataire_fournisseur': destinataire_fournisseur_obj,
            'devise_ao': 'EUR' # Ou à récupérer de l'AO/paramètres de l'appli
        }

        # 5. Rendre le template et générer le PDF
        template = template_env.get_template('rfq_template.html')
        html_output = template.render(context)

        # (Optionnel: sauvegarder le HTML pour débogage)
        # with open(f"debug_rfq_{ao.reference_ao}.html", "w", encoding="utf-8") as f:
        #     f.write(html_output)

        default_filename = f"AO_{ao.reference_ao}"
        if destinataire_fournisseur_obj:
            default_filename += f"_{destinataire_fournisseur_obj.nom.replace(' ', '_')}"
        default_filename += ".pdf"
        
        documents_path = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        file_path, _ = QFileDialog.getSaveFileName(
            parent_widget, 
            "Save Request for Quotation PDF",
            os.path.join(documents_path, default_filename),
            "PDF Files (*.pdf)"
        )

        if file_path:
            success = pdfkit.from_string(html_output, file_path, configuration=config)
            if success:
                print(f"RFQ PDF saved to: {file_path}")
                QMessageBox.information(parent_widget, "PDF Saved", f"RFQ PDF saved to:\n{file_path}")
                return True
            else:
                # ... (gestion d'erreur pdfkit failure)
                return False
        else:
            print("RFQ PDF generation cancelled by user.")
            return False

    except Exception as e:
        print(f"Error generating RFQ PDF for AO ID {ao_id}: {e}")
        import traceback
        traceback.print_exc()
        QMessageBox.critical(parent_widget, "PDF Generation Error", f"Could not generate RFQ PDF: {e}")
        return False
    finally:
        session.close()