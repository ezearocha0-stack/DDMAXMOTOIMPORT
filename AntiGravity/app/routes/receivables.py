from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required
from app.models.finance import CuentasPorCobrar
from app.extensions import db
from sqlalchemy.orm import joinedload

receivables_bp = Blueprint('accounts', __name__, url_prefix='/accounts')

@receivables_bp.route('/')
@login_required
def list_accounts():
    estado = request.args.get('estado', 'pendientes')
    
    from app.models.transactions import Facturas
    base_query = CuentasPorCobrar.query.join(Facturas).options(joinedload(CuentasPorCobrar.factura)).filter(Facturas.tipo == 'credito')
    
    if estado == 'pagadas':
        cuentas = base_query.filter(CuentasPorCobrar.estado == 'pagado').filter(Facturas.estado != 'anulada').order_by(CuentasPorCobrar.created_at.desc()).all()
    elif estado == 'todas':
        cuentas = base_query.order_by(CuentasPorCobrar.created_at.desc()).all()
    elif estado == 'anuladas':
        cuentas = base_query.filter(Facturas.estado == 'anulada').order_by(CuentasPorCobrar.created_at.desc()).all()
    else:
        cuentas = base_query.filter(CuentasPorCobrar.estado.in_(['pendiente', 'atrasado', 'al_dia', 'parcial'])).filter(CuentasPorCobrar.saldo > 0).filter(Facturas.estado != 'anulada').order_by(CuentasPorCobrar.created_at.desc()).all()
        
    return render_template('receivables/list.html', cuentas=cuentas, estado=estado)

@receivables_bp.route('/detail/<int:id>')
@login_required
def detail_account(id):
    cuenta = db.session.get(CuentasPorCobrar, id)
    if not cuenta:
        flash('Cuenta por cobrar no encontrada.', 'danger')
        return redirect(url_for('accounts.list_accounts'))
    return render_template('receivables/detail.html', cuenta=cuenta)
