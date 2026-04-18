from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models.entities import Proveedores, Productos
from app.models.transactions import Compras, DetalleCompra
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import joinedload
from flask_login import current_user

purchases_bp = Blueprint('purchases', __name__, url_prefix='/purchases')

@purchases_bp.route('/')
def list_purchases():
    estado = request.args.get('estado', 'pendientes')
    
    query = Compras.query
    if estado == 'pendientes':
        query = query.filter(Compras.estado.in_(['pendiente', 'parcial', 'pagada']))
    elif estado == 'anuladas':
        query = query.filter(Compras.estado == 'anulada')
        
    compras = query.options(joinedload(Compras.proveedor)).order_by(Compras.fecha.desc()).all()
    return render_template('purchases/list.html', compras=compras, estado_actual=estado)

@purchases_bp.route('/create', methods=['GET', 'POST'])
def create_purchase():
    if request.method == 'POST':
        proveedor_id = request.form.get('proveedor_id')
        tipo = request.form.get('tipo', 'contado')
        total = request.form.get('total')
        pago_inicial_str = request.form.get('pago_inicial', '0.0')
        
        # Listas del formulario dinámico
        producto_ids = request.form.getlist('producto_id[]')
        cantidades = request.form.getlist('cantidad[]')
        precios_unitarios = request.form.getlist('precio_unitario[]')
        itbis_unitarios = request.form.getlist('itbis_unitario[]')

        if not proveedor_id:
            flash('Debe seleccionar un proveedor.', 'danger')
            return redirect(url_for('purchases.create_purchase'))

        if not producto_ids or len(producto_ids) == 0:
            flash('Debe agregar al menos un producto a la compra.', 'danger')
            return redirect(url_for('purchases.create_purchase'))

        try:
            total_float = Decimal(total) if total else Decimal('0.0')
            
            # Crear Compra
            pago_inicial = Decimal(pago_inicial_str) if pago_inicial_str else Decimal('0.0')
            nueva_compra = Compras(
                proveedor_id=proveedor_id,
                tipo=tipo,
                costo_total=0.0, # Se actualizará después de calcular los ítems
                pago_inicial=pago_inicial,
                metodo_pago='Efectivo', # Predeterminado por ahora
                estado='pendiente'
            )
            db.session.add(nueva_compra)
            db.session.flush() # Obtener el nuevo ID de compra

            # Procesar ítems
            total_calculado = Decimal('0.0')
            for i in range(len(producto_ids)):
                prod_id = producto_ids[i]
                cant = int(cantidades[i])
                precio_u = Decimal(precios_unitarios[i])
                
                if cant <= 0 or precio_u < 0:
                    db.session.rollback()
                    flash('Las cantidades deben ser mayores a cero y los precios no pueden ser negativos.', 'danger')
                    return redirect(url_for('purchases.create_purchase'))
                    
                subt = cant * precio_u
                
                total_calculado += subt

                detalle = DetalleCompra(
                    compra_id=nueva_compra.id,
                    producto_id=prod_id,
                    cantidad=cant,
                    costo_unitario=precio_u
                )
                db.session.add(detalle)
                
                producto = Productos.query.get(prod_id)
                if producto:
                    if not producto.motocicleta:
                        producto.stock += cant
                        if producto.stock > 0:
                            producto.estado = 'disponible'
            
            # Usar el total calculado para estar a salvo de la manipulación en el lado del cliente
            nueva_compra.costo_total = total_calculado
            
            # Determinar estado de la compra original
            if tipo == 'contado' or pago_inicial >= total_calculado:
                nueva_compra.estado = 'pagada'
            elif pago_inicial > 0:
                nueva_compra.estado = 'parcial'
            else:
                nueva_compra.estado = 'pendiente'
            
            # Registrar cuenta por pagar si fue a crédito
            if tipo == 'credito':
                from app.models.finance import CuentasPorPagar
                
                # Validar pago inicial
                if pago_inicial > total_calculado:
                    db.session.rollback()
                    flash('El pago inicial no puede ser mayor al total de la compra.', 'danger')
                    return redirect(url_for('purchases.create_purchase'))
                    
                saldo_restante = total_calculado - pago_inicial
                
                cxp = CuentasPorPagar(
                    proveedor_id=proveedor_id,
                    compra_id=nueva_compra.id,
                    monto_total=total_calculado,
                    saldo=saldo_restante,
                    estado='pendiente' if saldo_restante == total_calculado else ('pagada' if saldo_restante <= 0 else 'parcial')
                )
                db.session.add(cxp)
                db.session.flush()

                # Generar las cuotas automáticamente
                if saldo_restante > 0:
                    meses_credito_str = request.form.get('numero_cuotas', '1')
                    try:
                        meses_credito = int(meses_credito_str)
                        if meses_credito < 1: meses_credito = 1
                    except:
                        meses_credito = 1

                    from app.models.finance import CuotasPorPagar
                    
                    monto_cuota = saldo_restante / Decimal(str(meses_credito))
                    monto_cuota = monto_cuota.quantize(Decimal('0.01'))
                    
                    from calendar import monthrange
                    def add_months(sourcedate, months):
                        month = sourcedate.month - 1 + months
                        year = sourcedate.year + month // 12
                        month = month % 12 + 1
                        day = min(sourcedate.day, monthrange(year, month)[1])
                        return sourcedate.replace(year=year, month=month, day=day)
                    
                    fecha_base = datetime.now()
                    
                    for i in range(1, meses_credito + 1):
                        fecha_ven = add_months(fecha_base, i)
                        cuota = CuotasPorPagar(
                            cuenta_pagar_id=cxp.id,
                            numero_cuota=i,
                            fecha_vencimiento=fecha_ven.date(),
                            monto=monto_cuota,
                            mora=0,
                            monto_pagado=0,
                            estado='pendiente'
                        )
                        db.session.add(cuota)
                

            
            db.session.commit()
            flash('Compra registrada exitosamente.', 'success')
            return redirect(url_for('purchases.list_purchases'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar la compra: {str(e)}', 'danger')
            return redirect(url_for('purchases.create_purchase'))

    # Cargar proveedores activos para el menú desplegable
    proveedores = Proveedores.query.filter_by(estado='activo').all()
    
    # Cargar productos disponibles que no sean motocicletas (o todos los productos) para el menú desplegable
    # Para un formulario de compra genérico, listamos todos los productos.
    productos = Productos.query.filter_by(estado='disponible').all()
    
    return render_template('purchases/create.html', proveedores=proveedores, productos=productos)

@purchases_bp.route('/detail/<int:id>')
def detail_purchase(id):
    compra = db.session.get(Compras, id)
    if not compra:
        flash('Compra no encontrada.', 'danger')
        return redirect(url_for('purchases.list_purchases'))
        
    return render_template('purchases/detail.html', compra=compra)
