from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models.entities import Clientes, Productos, Motocicletas
from app.models.transactions import Facturas, DetalleFactura
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import joinedload

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

@sales_bp.route('/')
def list_sales():
    estado = request.args.get('estado', 'pendientes')
    
    query = Facturas.query
    if estado == 'pendientes':
        query = query.filter(Facturas.estado != 'anulada')
    elif estado == 'anuladas':
        query = query.filter(Facturas.estado == 'anulada')
    facturas = query.options(joinedload(Facturas.cliente)).order_by(Facturas.fecha.desc()).all()
    return render_template('sales/list.html', facturas=facturas, estado_actual=estado)

@sales_bp.route('/create', methods=['GET', 'POST'])
def create_sale():
    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        tipo = request.form.get('tipo', 'contado')
        metodo_pago = request.form.get('metodo_pago', 'efectivo')
        descuento_global = Decimal(request.form.get('descuento_global') or '0.0')
        pago_inicial = Decimal(request.form.get('pago_inicial') or '0.0')
        tasa_interes_mensual = Decimal(request.form.get('tasa_interes_mensual') or '0.0')

        # líneas dinámicas
        producto_ids = request.form.getlist('producto_id[]')
        cantidades = request.form.getlist('cantidad[]')
        precios = request.form.getlist('precio[]')
        descuentos_linea = request.form.getlist('descuento_linea[]')

        if not cliente_id:
            flash('Debe seleccionar un cliente.', 'danger')
            return redirect(url_for('sales.create_sale'))

        if not producto_ids or len(producto_ids) == 0:
            flash('La factura debe tener al menos un producto.', 'danger')
            return redirect(url_for('sales.create_sale'))

        if descuento_global < 0 or pago_inicial < 0 or tasa_interes_mensual < 0:
            flash('Los descuentos globales, pagos iniciales y tasas de interés no pueden ser negativos.', 'danger')
            return redirect(url_for('sales.create_sale'))

        try:
            # Crear registro maestro de factura
            nueva_factura = Facturas(
                cliente_id=cliente_id,
                usuario_id=1,  # Por defecto al admin por ahora
                tipo=tipo,
                metodo_pago=metodo_pago,
                subtotal=Decimal('0.0'),
                descuento=descuento_global,
                total=Decimal('0.0'),
                pago_inicial=pago_inicial,
                estado='pagada' if tipo == 'contado' else 'pendiente'
            )
            db.session.add(nueva_factura)
            db.session.flush()

            subtotal_calculado = Decimal('0.0')
            moto_ids_agregadas = set()
            
            # Crear detalles de factura
            for i in range(len(producto_ids)):
                prod_id = producto_ids[i]
                cant = int(cantidades[i])
                precio_u = Decimal(precios[i])
                desc_lin = Decimal(descuentos_linea[i] or '0.0')
                
                if cant <= 0 or precio_u < 0 or desc_lin < 0:
                    db.session.rollback()
                    flash('Las cantidades deben ser mayores a cero. Precios y descuentos no pueden ser negativos.', 'danger')
                    return redirect(url_for('sales.create_sale'))
                
                producto = Productos.query.get(prod_id)
                if not producto:
                    db.session.rollback()
                    flash(f'Error: Producto desconocido.', 'danger')
                    return redirect(url_for('sales.create_sale'))
                    
                if producto.motocicleta:
                    if prod_id in moto_ids_agregadas:
                        db.session.rollback()
                        flash('Error: No puede incluir la misma motocicleta más de una vez en la factura (VIN Único).', 'danger')
                        return redirect(url_for('sales.create_sale'))
                    moto_ids_agregadas.add(prod_id)
                    
                    
                    if producto.motocicleta.estado != 'en inventario':
                        db.session.rollback()
                        flash('Error: Una motocicleta seleccionada ya no está disponible.', 'danger')
                        return redirect(url_for('sales.create_sale'))
                    
                    cant = 1
                    producto.motocicleta.estado = 'vendida'
                else:
                    if cant > producto.stock:
                        db.session.rollback()
                        flash(f'Error: Stock insuficiente para {producto.nombre}. Disp: {producto.stock}', 'danger')
                        return redirect(url_for('sales.create_sale'))
                    
                    producto.stock -= cant
                    if producto.stock <= 0:
                        producto.estado = 'agotado'
                
                line_total_before_discount = cant * precio_u
                line_total = line_total_before_discount - desc_lin
                
                subtotal_calculado += line_total_before_discount

                detalle = DetalleFactura(
                    factura_id=nueva_factura.id,
                    producto_id=prod_id,
                    cantidad=cant,
                    precio_unitario=precio_u,
                    descuento=desc_lin
                )
                db.session.add(detalle)

            # Aplicar descuento global a la suma de los subtotales de línea (que ya tienen descuentos aplicados)
            # En realidad, la forma estándar: El subtotal es la suma de (Cant * Precio).
            # Descuentos totales = suma de descuentos de línea + descuento global.
            # Total = Subtotal + ITBIS - Descuentos totales
            
            total_descuento_lineas = sum([Decimal(d or '0.0') for d in descuentos_linea])
            total_descuentos = total_descuento_lineas + descuento_global
            
            total_final = subtotal_calculado - total_descuentos
            
            if pago_inicial > total_final:
                db.session.rollback()
                flash('El pago inicial no puede ser mayor al total de la factura.', 'danger')
                return redirect(url_for('sales.create_sale'))

            nueva_factura.subtotal = subtotal_calculado
            nueva_factura.total = total_final
            
            # Si es crédito, generar cuentas por cobrar
            if tipo == 'credito':
                meses_credito_str = request.form.get('meses_credito', '1')
                try:
                    meses_credito = int(meses_credito_str)
                    if meses_credito < 1:
                        meses_credito = 1
                except:
                    meses_credito = 1
                    
                from app.models.finance import CuentasPorCobrar, Cuotas
                saldo_base = total_final - pago_inicial
                if saldo_base < 0:
                    saldo_base = Decimal('0.0')
                
                interes_total = Decimal('0.0')
                if saldo_base > 0 and tasa_interes_mensual > 0:
                    interes_total = saldo_base * (tasa_interes_mensual / Decimal('100.0')) * Decimal(str(meses_credito))
                
                interes_total = interes_total.quantize(Decimal('0.01'))
                total_financiado = saldo_base + interes_total
                
                cxc = CuentasPorCobrar(
                    factura_id=nueva_factura.id,
                    monto_total=total_final + interes_total,
                    saldo=total_financiado,
                    estado='pendiente' if total_financiado > 0 else 'pagado'
                )
                db.session.add(cxc)
                db.session.flush() # Obtener cx.id para las cuotas
                
                # Generar las cuotas automáticamente
                if total_financiado > 0:
                    monto_cuota = total_financiado / Decimal(str(meses_credito))
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
                        cuota = Cuotas(
                            cuenta_id=cxc.id,
                            numero_cuota=i,
                            fecha_vencimiento=fecha_ven.date(),
                            monto=monto_cuota,
                            mora=0,
                            monto_pagado=0,
                            estado='pendiente'
                        )
                        db.session.add(cuota)



            # Auditoría
            from app.models.auth import Auditoria
            from flask_login import current_user
            audit_log = Auditoria(
                usuario_id=current_user.id if current_user.is_authenticated else 1,
                tabla='facturas',
                registro_id=nueva_factura.id,
                accion='insertar'
            )
            db.session.add(audit_log)

            db.session.commit()
            flash('Venta registrada exitosamente.', 'success')
            return redirect(url_for('sales.detail_sale', id=nueva_factura.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar la venta: {str(e)}', 'danger')
            return redirect(url_for('sales.create_sale'))

    clientes = Clientes.query.all()
    # Traemos productos y motocicletas disponibles
    productos = []
    
    # 1. Motocicletas disponibles (estado='en inventario')
    motos_disponibles = Motocicletas.query.filter_by(estado='en inventario').all()
    for m in motos_disponibles:
        productos.append({
            'tipo': 'moto',
            'id': m.producto_id,
            'moto_id': m.id,
            'nombre': f"MOTO: {m.marca} {m.modelo} (VIN: {m.vin})",
            'precio': m.producto.precio
        })
        
    # 2. Productos regulares (piezas/accesorios)
    # Buscamos productos disponibles que no tengan vinculada una motocicleta
    prod_disponibles = Productos.query.filter_by(estado='disponible').all()
    for p in prod_disponibles:
        # Excluimos si es una motocicleta
        if not p.motocicleta:
            productos.append({
                'tipo': 'estandar',
                'id': p.id,
                'moto_id': '',
                'nombre': p.nombre,
                'precio': p.precio
            })

    return render_template('sales/create.html', clientes=clientes, productos=productos)

@sales_bp.route('/detail/<int:id>')
def detail_sale(id):
    factura = db.session.get(Facturas, id)
    if not factura:
        flash('Factura no encontrada.', 'danger')
        return redirect(url_for('sales.list_sales'))
    
    # Calcular algunas estructuras auxiliares para la vista si es necesario
    total_descuento_lineas = sum([d.descuento for d in factura.detalles])
    descuento_total_absoluto = total_descuento_lineas + factura.descuento

    return render_template('sales/detail.html', factura=factura, desc_total=descuento_total_absoluto, desc_lineas=total_descuento_lineas)

@sales_bp.route('/return/<int:id>', methods=['POST'])
def return_sale(id):
    factura = db.session.get(Facturas, id)
    if not factura:
        flash('Factura no encontrada.', 'danger')
        return redirect(url_for('sales.list_sales'))
        
    motivo = request.form.get('motivo', 'Devolución estándar')
    detalle_ids = request.form.getlist('detalle_ids[]')
    
    if not detalle_ids:
        flash('Debe seleccionar al menos un artículo para devolver.', 'warning')
        return redirect(url_for('sales.detail_sale', id=factura.id))
        
    from app.models.transactions import Devoluciones
    from flask_login import current_user
    from decimal import Decimal
    
    monto_devuelto = Decimal('0.0')
    
    try:
        # Prevent returning the same motorcycle twice. 
        # Check carefully if the user is trying to return an already returned item.
        # But our DB structure doesn't easily track per-detail returns unless we check the motorcycle status
        # For simplicity, if we re-stock the motorcycle, its state changes to 'en inventario'.
        # We will only allow returning motorcycles if they are 'vendida'.
        
        for d_id in detalle_ids:
            detalle = db.session.get(DetalleFactura, int(d_id))
            if not detalle or detalle.factura_id != factura.id:
                continue
                
            # Calcular monto neto de esta línea (precio * cant - descuento)
            monto_linea = (Decimal(str(detalle.precio_unitario)) * detalle.cantidad) - Decimal(str(detalle.descuento or '0.0'))
            
            # Recuperar Inventario de Moto
            moto = detalle.producto.motocicleta if detalle.producto else None
            if moto:
                if moto.estado == 'vendida':
                    moto.estado = 'en inventario' # Recuperación
                    monto_devuelto += monto_linea
                else:
                    flash(f'La motocicleta VIN {moto.vin} ya fue devuelta o no es recuperable.', 'warning')
                    continue
            else:
                # Recuperar Productos regulares sumando el stock real
                detalle.producto.stock += detalle.cantidad
                if detalle.producto.stock > 0:
                    detalle.producto.estado = 'disponible'
                monto_devuelto += monto_linea
                
        if monto_devuelto > 0:
            monto_total_devolucion = monto_devuelto
            
            nueva_devolucion = Devoluciones(
                factura_id=factura.id,
                usuario_id=current_user.id if current_user.is_authenticated else 1,
                motivo=motivo,
                monto_devuelto=monto_total_devolucion
            )
            db.session.add(nueva_devolucion)
            
            saldo_deducido = Decimal('0.0')
            # Operar con CuentasPorCobrar
            if factura.cuenta_por_cobrar:
                # Si tiene deuda, deducimos el monto de la deuda para perdonarla
                if factura.cuenta_por_cobrar.saldo > 0:
                    deduccion = min(factura.cuenta_por_cobrar.saldo, monto_total_devolucion)
                    factura.cuenta_por_cobrar.saldo -= deduccion
                    saldo_deducido = deduccion
                    if factura.cuenta_por_cobrar.saldo == 0:
                        factura.cuenta_por_cobrar.estado = 'pagado'
                        
                    # Repartir el perdón de deuda entre cuotas pendientes
                    monto_restante_desc = saldo_deducido
                    from app.models.finance import Cuotas
                    cuotas_pendientes = Cuotas.query.filter_by(cuenta_id=factura.cuenta_por_cobrar.id).filter(Cuotas.estado != 'pagada').order_by(Cuotas.numero_cuota).all()
                    
                    for cuota in cuotas_pendientes:
                        if monto_restante_desc <= 0:
                            break
                        
                        deuda_cuota = cuota.monto - cuota.monto_pagado
                        if monto_restante_desc >= deuda_cuota:
                            cuota.monto_pagado = cuota.monto
                            cuota.estado = 'pagada'
                            monto_restante_desc -= deuda_cuota
                        else:
                            cuota.monto_pagado += monto_restante_desc
                            cuota.estado = 'parcial'
                            monto_restante_desc = Decimal('0.0')
                        
            # Recalcular estado de la factura basándonos en el histórico de devoluciones
            total_devuelto_hist = sum(d.monto_devuelto for d in factura.devoluciones if d.id is not None)
            total_historico = total_devuelto_hist + monto_total_devolucion
            
            if total_historico >= factura.total:
                factura.estado = 'anulada'
                if factura.cuenta_por_cobrar and factura.cuenta_por_cobrar.saldo == 0:
                    factura.cuenta_por_cobrar.estado = 'anulada'
            else:
                if factura.cuenta_por_cobrar and factura.cuenta_por_cobrar.saldo > 0:
                    factura.estado = 'pendiente'
                else:
                    factura.estado = 'dev. parcial'
                        

            
            # Auditoría
            from app.models.auth import Auditoria
            from flask_login import current_user
            audit_log = Auditoria(
                usuario_id=current_user.id if current_user.is_authenticated else 1,
                tabla='devoluciones',
                registro_id=nueva_devolucion.id,
                accion='insertar'
            )
            db.session.add(audit_log)
            
            db.session.commit()
            flash(f'Devolución de ${monto_total_devolucion:,.2f} procesada exitosamente.', 'success')
        else:
            flash('No se proceso ninguna devolución válida (los artículos ya fueron devueltos).', 'info')
            
        return redirect(url_for('sales.detail_sale', id=factura.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error en devolución: {str(e)}', 'danger')
        return redirect(url_for('sales.detail_sale', id=factura.id))
