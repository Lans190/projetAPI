from flask import request, jsonify
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import admin_bp  # Assurez-vous que l'importation du blueprint est correcte ici
import psycopg2
import psycopg2.extras

# Configurations de la base de données
DB_host = "localhost"
DB_name = "DATA.API"
DB_user = "postgres"
DB_pass = "Lass5920@"

@admin_bp.route('/connection', methods=['POST'])
def login():
    data = request.get_json()
    recup_user = data.get("username")
    recup_pass = data.get("password")

    conn = psycopg2.connect(host=DB_host, dbname=DB_name, user=DB_user, password=DB_pass)
    parcours = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Exécutez la requête SQL pour vérifier les identifiants utilisateur
    parcours.execute("SELECT * FROM users WHERE prenom = %s AND pass_word = %s", (recup_user, recup_pass))
    var_recuper = parcours.fetchone()

    parcours.close()
    conn.close()

    if var_recuper:
        # Si les identifiants sont valides, créez le token d'accès en fonction du rôle de l'utilisateur
        role = var_recuper["roles"]
        recup_token = create_access_token(identity={'id': var_recuper["id_users"], 'role': role})
        return jsonify({"recup_token": recup_token})
    else:
        # Sinon, retournez un message d'erreur avec le code HTTP 401
        return jsonify({"message": "Invalid user credentials"}), 401




# création d'utilisateurs
@admin_bp.route('/create_user', methods=['POST'])
@jwt_required()
def create_user():
    identity = get_jwt_identity()
    if identity['roles'] != 'admin':
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    role = data.get("roles")

    conn = psycopg2.connect(host=DB_host, dbname=DB_name, user=DB_user, password=DB_pass)
    parcours = conn.cursor()
    parcours.execute("INSERT INTO users (username, pass_word, roles) VALUES (%s, %s, %s)", (username, password, role))
    conn.commit()
    parcours.close()
    conn.close()

    return jsonify({"message": "User created successfully"}), 201


# Validation, demande de suppression ou demande de modification des prompts
@admin_bp.route('/prompts/<int:prompt_id>', methods=['PATCH', 'DELETE'])
@jwt_required()
def manage_prompt(prompt_id):
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    conn = psycopg2.connect(host=DB_host, dbname=DB_name, user=DB_user, password=DB_pass)

    if request.method == 'PATCH':
        data = request.get_json()
        new_status = data.get("status")
        parcours = conn.cursor()
        parcours.execute("UPDATE prompts SET status = %s WHERE id = %s", (new_status, prompt_id))
        conn.commit()
        parcours.close()
        conn.close()
        return jsonify({"message": "Prompt status updated"}), 200

    elif request.method == 'DELETE':
        parcours = conn.cursor()
        parcours.execute("DELETE FROM prompts WHERE id_prompt = %s", (prompt_id,))
        conn.commit()
        parcours.close()
        conn.close()
        return jsonify({"message": "Prompt deleted"}), 200
    


# ajout des prompts
@admin_bp.route('/prompts_ajouter', methods=['POST'])
@jwt_required()
def add_prompt():
    identity = get_jwt_identity()
    if identity['role'] not in ['admin', 'user']:
        return jsonify({"message": "Access forbidden: Admins and Users only"}), 403

    data = request.get_json()
    prompt_text = data.get("prompt_text")
    status = data.get("status")  # Peut-être facultatif selon votre structure de base de données

    conn = psycopg2.connect(host=DB_host, dbname=DB_name, user=DB_user, password=DB_pass)
    parcours = conn.cursor()
    parcours.execute("INSERT INTO prompts (titre, contenu) VALUES (%s, %s)", (prompt_text, status))
    conn.commit()
    parcours.close()
    conn.close()

    return jsonify({"message": "Prompt added successfully"}), 201

    


#Visualisations des prompts
@admin_bp.route('/prompts', methods=['GET'])
@jwt_required()
def view_prompts():
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    conn = psycopg2.connect(host=DB_host, dbname=DB_name, user=DB_user, password=DB_pass)
    parcours = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    parcours.execute("SELECT * FROM prompts")
    prompts = parcours.fetchall()
    parcours.close()
    conn.close()

    return jsonify(prompts), 200
  
# Ajouter un utilisateur à un groupe
@admin_bp.route('/add_user_to_group', methods=['POST'])
@jwt_required()
def add_user_to_group():
    identity = get_jwt_identity()
    if identity['role'] == 'admin':
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    data = request.get_json()
    groupe_id = data.get("id_groupe")
    group_name = data.get("group_name")

    conn = psycopg2.connect(host=DB_host, dbname=DB_name, user=DB_user, password=DB_pass)
    parcours = conn.cursor()
    parcours.execute("INSERT INTO groupes (id_groupe,group_name) VALUES (%s, %s)", (groupe_id, group_name))
    conn.commit()
    parcours.close()
    conn.close()

    return jsonify({"message": "User added to group successfully"}), 201


# Suppression d'utilisateurs
@admin_bp.route('/delete_user/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    conn = psycopg2.connect(host=DB_host, dbname=DB_name, user=DB_user, password=DB_pass)
    parcours = conn.cursor()
    parcours.execute("DELETE FROM users WHERE id_users = %s", (user_id,))
    conn.commit()
    parcours.close()
    conn.close()

    return jsonify({"message": "User deleted successfully"}), 200



















