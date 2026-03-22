from flask import Flask, redirect, url_for, request
from app.config.settings import Config
from app.extensions import db, login_manager
from flask_login import current_user

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        # Importar modelos para que se registren con SQLAlchemy
        from app import models
        
        # Registraremos los blueprints aquí más tarde
        from app.routes.auth import auth_bp
        from app.routes.main import main_bp
        from app.routes.clients import clients_bp
        from app.routes.inventory import inventory_bp
        from app.routes.suppliers import suppliers_bp
        from app.routes.purchases import purchases_bp
        from app.routes.sales import sales_bp
        from app.routes.receivables import receivables_bp
        from app.routes.payments import payments_bp
        from app.routes.payables import payables_bp
        from app.routes.cash_movements import cash_movements_bp
        from app.routes.reports import reports_bp
        from app.routes.audit import audit_bp
        
        from app.utils.audit_logger import register_audit_listeners
        register_audit_listeners()
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(clients_bp)
        app.register_blueprint(inventory_bp)
        app.register_blueprint(suppliers_bp)
        app.register_blueprint(purchases_bp)
        app.register_blueprint(sales_bp)
        app.register_blueprint(receivables_bp)
        app.register_blueprint(payments_bp)
        app.register_blueprint(payables_bp)
        app.register_blueprint(cash_movements_bp)
        app.register_blueprint(reports_bp)
        app.register_blueprint(audit_bp)

    @app.before_request
    def require_login():
        allowed_endpoints = ['auth.login', 'auth.logout', 'static']
        if request.endpoint and request.endpoint not in allowed_endpoints:
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))

    return app
