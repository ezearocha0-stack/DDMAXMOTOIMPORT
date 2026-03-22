from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required
from app.models.finance import CuentasPorCobrar
from app.extensions import db

receivables_bp = Blueprint('accounts', __name__, url_prefix='/accounts')

@receivables_bp.route('/')
@login_required
def list_accounts():
    cuentas = CuentasPorCobrar.query.filter(CuentasPorCobrar.saldo > 0).order_by(CuentasPorCobrar.created_at.desc()).all()
    return render_template('receivables/list.html', cuentas=cuentas)

@receivables_bp.route('/detail/<int:id>')
@login_required
def detail_account(id):
    cuenta = db.session.get(CuentasPorCobrar, id)
    if not cuenta:
        flash('Cuenta por cobrar no encontrada.', 'danger')
        return redirect(url_for('accounts.list_accounts'))
    return render_template('receivables/detail.html', cuenta=cuenta)
