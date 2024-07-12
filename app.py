from flask import Flask
from flask_jwt_extended import JWTManager
from bleuprint.ADMIN import admin_bp
from bleuprint.USERS import user_bp

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = 'lucien123'
jwt = JWTManager(app)



app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)

if __name__ == '__main__':
    app.run(debug=True)
