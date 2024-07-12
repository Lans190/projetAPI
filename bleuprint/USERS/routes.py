from flask import request, jsonify
from flask_jwt_extended import create_access_token

from flask_jwt_extended import jwt_required, get_jwt_identity
from . import user_bp
import psycopg2
import psycopg2.extras

                    # Configguration de la base de donnée
DB_host = "localhost"
DB_name = "DATA.API"
DB_user = "postgres"
DB_pass = "Lass5920@"

                    #définition de l'endpoint de la base de donnée

@user_bp.route('/connection', methods=['POST'])
def login():
    data = request.get_json()
    recup_user = data.get("username")
    recup_pass = data.get("password")
                       
                       # Connection ala base de donnée

    conn = psycopg2.connect(host=DB_host, dbname=DB_name, user=DB_user, password=DB_pass)
    parcours = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                     
                      # Exécution de la requête SQL
   
    parcours.execute("SELECT * FROM users WHERE prenom = %s AND pass_word = %s", (recup_user, recup_pass))
    var_recuper = parcours.fetchone()
    parcours.close()
    conn.close()
# Génération du TOKEN JWT
    if var_recuper:
        recup_token = create_access_token(identity={'id': var_recuper["id_users"], 'role': 'users'})
        return jsonify({"recup_token": recup_token})
    else:
        return jsonify({"message": "Invalid user credentials"}), 401
    

# Endpoint pour soumettre un Prompt à vendre
@user_bp.route('/prompts', methods=['POST'])
@jwt_required()
def propose_prompt():
    current_user = get_jwt_identity()
    data = request.get_json()

    titre = data.get('titre')
    contenu = data.get('contenu')
    prix = data.get('prix')

    conn = psycopg2.connect(host=DB_host, dbname=DB_name, user=DB_user, password=DB_pass)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO prompts (titre, contenu, prix, users_id) VALUES (%s, %s, %s, %s)",
                   (titre, contenu, prix, current_user['id']))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Prompt submitted successfully"}), 201

# Endpoint pour voter pour un Prompt en attente de validation
@user_bp.route('/prompts/<int:prompt_id>/vote', methods=['POST'])
@jwt_required()
def vote_prompt(prompt_id):
    current_user = get_jwt_identity()

    conn = psycopg2.connect(host=DB_host, dbname=DB_name, user=DB_user, password=DB_pass)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO votes (id_prompt, users_id) VALUES (%s, %s)",
                   (prompt_id, current_user['id']))
    conn.commit()
    cursor.close()
    conn.close()


# Endpoint pour noter un prompt
@user_bp.route('/notes_prompt/<int:prompt_id>', methods=['POST'])
@jwt_required()
def note_prompt(prompt_id):
    data = request.get_json()
    note = data.get("note")

    if note is None:
        return jsonify({"message": "La note est requise"}), 400

    try:
        note = float(note)  # Convertir en float
    except ValueError:
        return jsonify({"message": "La note doit être un nombre"}), 400

    if note < -10 or note > 10:
        return jsonify({"message": "La note doit être comprise entre -10 et +10"}), 400

    current_user = get_jwt_identity()

    conn = psycopg2.connect(host=DB_host, dbname=DB_name, user=DB_user, password=DB_pass)
    cursor = conn.cursor()

    try:
        # Vérifier si le prompt existe et récupérer l'utilisateur créateur du prompt
        cursor.execute("SELECT users_id FROM prompts WHERE id_prompts = %s", (prompt_id,))
        prompt = cursor.fetchone()

        if not prompt:
            return jsonify({"message": "Prompt non trouvé"}), 404

        prompt_user_id = prompt[0]

        # Vérifier si l'utilisateur est membre du groupe du prompt
        cursor.execute("SELECT COUNT(*) FROM groupes_membres WHERE id_groupe = (SELECT id_groupe FROM groupes_membres WHERE users_id = %s) AND users_id = %s", (prompt_user_id, current_user['id']))
        is_group_member = cursor.fetchone()

        if not is_group_member:
            return jsonify({"message": "Vous n'êtes pas membre du groupe de ce prompt"}), 403

        # Vérifier si l'utilisateur a déjà noté ce prompt
        cursor.execute("SELECT COUNT(*) FROM notes WHERE users_id = %s AND prompts_id = %s", (current_user['id'], prompt_id))
        already_rated = cursor.fetchone()

        if already_rated[0] > 0:
            return jsonify({"message": "Vous avez déjà noté ce prompt"}), 403

        # Insérer la note dans la table des notes
        cursor.execute("INSERT INTO notes (note, prompts_id, users_id) VALUES (%s, %s, %s)", (note, prompt_id, current_user['id']))
        conn.commit()

        # Calculer la moyenne des notes pour ce prompt
        cursor.execute("SELECT AVG(note) FROM notes WHERE prompts_id = %s", (prompt_id,))
        average_rating = cursor.fetchone()[0]

        # Calculer le nouveau prix du prompt
        new_price = 1000 * (1 + average_rating)

        # Mettre à jour le prix du prompt dans la base de données
        cursor.execute("UPDATE prompts SET prix = %s WHERE id_prompts = %s", (new_price, prompt_id))
        conn.commit()

        return jsonify({"message": "Note ajoutée avec succès", "nouveau_prix": new_price}), 200

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({"message": "Erreur lors de l'opération sur la base de données", "error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

   
      
      
      