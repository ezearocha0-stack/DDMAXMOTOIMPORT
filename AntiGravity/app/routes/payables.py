from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.extensions import db
from app.models.finance import CuentasPorPagar, PagosProveedor
from flask_login import current_user, login_required
from decimal import Decimal

payables_bp = Blueprint('payables', __name__, url_prefix='/payables')

@payables_bp.route('/')
@login_required
def list_accounts():
    cuentas = CuentasPorPagar.query.filter(CuentasPorPagar.saldo > 0).order_by(CuentasPorPagar.created_at.desc()).all()
    return render_template('payables/list.html', cuentas=cuentas)

@payables_bp.route('/<int:id>')
@login_required
def detail_account(id):
    cuenta = db.session.get(CuentasPorPagar, id)
    if not cuenta:
        flash('Cuenta por pagar no encontrada.', 'danger')
        return redirect(url_for('payables.list_accounts'))
    return render_template('payables/detail.html', cuenta=cuenta)

@payables_bp.route('/payment', methods=['GET', 'POST'])
@login_required
def create_payment():
    if request.method == 'POST':
        cuenta_pagar_id = request.form.get('cuenta_pagar_id')
        monto_str = request.form.get('monto')
        
        if not cuenta_pagar_id or not monto_str:
            flash('Debe seleccionar una cuenta y especificar el monto.', 'danger')
            return redirect(url_for('payables.create_payment'))
            
        try:
            monto_pagado = Decimal(monto_str)
            if monto_pagado <= 0:
                flash('El monto a pagar debe ser mayor a cero.', 'danger')
                return redirect(url_for('payables.create_payment'))
                
            cuenta = CuentasPorPagar.query.get(cuenta_pagar_id)
            if not cuenta:
                flash('La cuenta especificada no existe.', 'warning')
                return redirect(url_for('payables.create_payment'))
                
            if monto_pagado > cuenta.saldo:
                flash(f'El monto ingresado (${monto_pagado:,.2f}) supera el saldo (${cuenta.saldo:,.2f}).', 'danger')
                return redirect(url_for('payables.create_payment'))
                
            # Log payment
            from datetime import datetime
            nuevo_pago = PagosProveedor(
                cuenta_pagar_id=cuenta.id,
                usuario_id=current_user.id if current_user.is_authenticated else 1,
                monto=monto_pagado,
                referencia=f"Transacción OP-{datetime.now().timestamp()}"
            )
            db.session.add(nuevo_pago)
            
            # Reduce saldo
            cuenta.saldo -= monto_pagado
            
            # Update state if paid in full
            if cuenta.saldo <= 0:
                cuenta.saldo = 0
                cuenta.estado = 'pagada'
                
                # Update underlying purchase
                if cuenta.compra:
                    cuenta.compra.estado = 'pagada'
            elif cuenta.saldo < cuenta.monto_total:
                cuenta.estado = 'parcial'
                if cuenta.compra:
                    cuenta.compra.estado = 'parcial'
                
            # --- NUEVA LÓGICA: MovimientosCaja ---
            from app.models.finance import MovimientosCaja
            movimiento = MovimientosCaja(
                usuario_id=current_user.id if current_user.is_authenticated else 1,
                tipo_movimiento='egreso',
                monto=monto_pagado,
                concepto=f'Pago a CxP Compra #{cuenta.compra_id} - Proveedor {cuenta.proveedor_id}'
            )
            db.session.add(movimiento)
                
            db.session.commit()
            flash(f'Pago de ${monto_pagado:,.2f} aplicado exitosamente a la cuenta del proveedor.', 'success')
            return redirect(url_for('payables.list_accounts'))
            
        except ValueError:
            flash('Monto inválido. Por favor ingrese un número válido.', 'danger')
            return redirect(url_for('payables.create_payment'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar el pago: {str(e)}', 'danger')
            return redirect(url_for('payables.create_payment'))

    # GET Request: Fetch pending accounts
    cuenta_id_preselected = request.args.get('cuenta_pagar_id', type=int)
    cuentas_pendientes = CuentasPorPagar.query.filter(CuentasPorPagar.estado != 'pagada').all()
    return render_template('payables/create.html', cuentas=cuentas_pendientes, preselected=cuenta_id_preselected)
