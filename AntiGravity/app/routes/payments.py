from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.extensions import db
from app.models.finance import CuentasPorCobrar, Pagos
from flask_login import current_user
from decimal import Decimal

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/create', methods=['GET', 'POST'])
def create_payment():
    if request.method == 'POST':
        cuenta_id = request.form.get('cuenta_id')
        monto_str = request.form.get('monto')
        
        if not cuenta_id or not monto_str:
            flash('Debe seleccionar una cuenta y especificar el monto.', 'danger')
            return redirect(url_for('payments.create_payment'))
            
        try:
            monto_pagado = Decimal(monto_str)
            if monto_pagado <= 0:
                flash('El monto a pagar debe ser mayor a cero.', 'danger')
                return redirect(url_for('payments.create_payment'))
                
            cuenta = CuentasPorCobrar.query.get(cuenta_id)
            if not cuenta:
                flash('La cuenta especificada no existe.', 'warning')
                return redirect(url_for('payments.create_payment'))
                
            if cuenta.estado in ['pagado', 'anulada']:
                flash('No se pueden registrar pagos a una cuenta pagada o anulada.', 'danger')
                return redirect(url_for('payments.create_payment'))
                
            if monto_pagado > cuenta.saldo:
                flash(f'El monto ingresado (${monto_pagado:,.2f}) supera el saldo pendiente (${cuenta.saldo:,.2f}).', 'danger')
                return redirect(url_for('payments.create_payment'))
                
            # Log payment
            nuevo_pago = Pagos(
                cuenta_id=cuenta.id,
                usuario_id=current_user.id if current_user.is_authenticated else 1,
                monto=monto_pagado
            )
            db.session.add(nuevo_pago)
            
            # Reduce saldo
            cuenta.saldo -= monto_pagado
            
            # Repartir pago entre cuotas pendientes
            monto_restante = monto_pagado
            from app.models.finance import Cuotas
            cuotas_pendientes = Cuotas.query.filter_by(cuenta_id=cuenta.id).filter(Cuotas.estado != 'pagada').order_by(Cuotas.numero_cuota).all()
            
            for cuota in cuotas_pendientes:
                if monto_restante <= 0:
                    break
                
                deuda_cuota = cuota.monto - cuota.monto_pagado
                if monto_restante >= deuda_cuota:
                    cuota.monto_pagado = cuota.monto
                    cuota.estado = 'pagada'
                    monto_restante -= deuda_cuota
                else:
                    cuota.monto_pagado += monto_restante
                    cuota.estado = 'parcial'
                    monto_restante = Decimal('0.0')

            # Update state if paid in full
            if cuenta.saldo <= 0:
                cuenta.saldo = Decimal('0.0')
                cuenta.estado = 'pagado'
                
                # Sincronizar estado de la factura
                if cuenta.factura:
                    cuenta.factura.estado = 'completada'
                
            # --- NUEVA LÓGICA: MovimientosCaja ---
            from app.models.finance import MovimientosCaja
            movimiento = MovimientosCaja(
                usuario_id=current_user.id if current_user.is_authenticated else 1,
                tipo_movimiento='ingreso',
                monto=monto_pagado,
                concepto=f'Abono a CxC Factura #{cuenta.factura_id}'
            )
            db.session.add(movimiento)
                
            db.session.commit()
            flash(f'Pago de ${monto_pagado:,.2f} aplicado exitosamente a la cuenta.', 'success')
            return redirect(url_for('accounts.detail_account', id=cuenta.id))
            
        except ValueError:
            flash('Monto inválido. Por favor ingrese un número válido.', 'danger')
            return redirect(url_for('payments.create_payment'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar el pago: {str(e)}', 'danger')
            return redirect(url_for('payments.create_payment'))

    # GET Request: Fetch specific account
    cuenta_id = request.args.get('cuenta_id', type=int)
    if cuenta_id:
        cuenta = CuentasPorCobrar.query.get(cuenta_id)
        if cuenta and cuenta.estado not in ['pagado', 'anulada']:
            return render_template('payments/create.html', cuenta=cuenta)
            
    # Fallback to listing strategy in case it's navigated manually without args
    cuentas_pendientes = CuentasPorCobrar.query.filter(CuentasPorCobrar.estado.notin_(['pagado', 'anulada'])).all()
    return render_template('payments/create.html', cuentas=cuentas_pendientes, preselected=cuenta_id)
