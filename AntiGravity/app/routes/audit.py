from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.auth import Auditoria
from app.extensions import db

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

@audit_bp.route('/')
@login_required
def list_audits():
    # Solo administradores (rol 1) deberían ver esto, pero por ahora lo dejamos genérico
    logs = Auditoria.query.order_by(Auditoria.fecha.desc()).limit(200).all()
    return render_template('audit/list.html', logs=logs)
