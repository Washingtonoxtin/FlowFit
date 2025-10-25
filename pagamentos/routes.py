from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Cliente, Pagamento
from app.utils import login_required, calcular_status_cliente
from app.extensions import db
from datetime import date, datetime

pagamentos_bp = Blueprint('pagamentos', __name__)

@pagamentos_bp.route('/relatorio_inadimplentes')
@login_required
def relatorio_inadimplentes():
    from app.utils import get_current_user
    
    clientes = Cliente.query.filter_by(ativo=True).all()
    inadimplentes = []
    
    for cliente in clientes:
        status = calcular_status_cliente(cliente)
        
        if status == "Em atraso":
            meses_atraso, valor_devido = cliente.calcular_meses_atraso()
            
            try:
                import calendar
                ultimo_dia_mes = calendar.monthrange(date.today().year, date.today().month)[1]
                dia_vencimento_mes = min(cliente.dia_vencimento, ultimo_dia_mes)
                vencimento_atual = date(date.today().year, date.today().month, dia_vencimento_mes)
                dias_atraso = (date.today() - vencimento_atual).days
            except:
                dias_atraso = 0
            
            inadimplentes.append({
                'cliente': cliente,
                'meses_atraso': max(1, meses_atraso),
                'valor_devido': valor_devido if valor_devido > 0 else cliente.valor_mensalidade,
                'dias_atraso': max(0, dias_atraso)
            })
    
    inadimplentes.sort(key=lambda x: x['meses_atraso'], reverse=True)
    usuario_atual = get_current_user()
    hoje = date.today()
    
    return render_template('inadimplentes.html', inadimplentes=inadimplentes, hoje=hoje, current_user=usuario_atual)

@pagamentos_bp.route('/registrar_pagamento_manual/<int:cliente_id>', methods=['POST'])
@login_required
def registrar_pagamento_manual(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    
    valor_pago = float(request.form.get('valor_pago'))
    data_pagamento = request.form.get('data_pagamento')
    mes_ref = int(request.form.get('mes_referencia'))
    ano_ref = int(request.form.get('ano_referencia'))
    observacoes = request.form.get('observacoes', '')
    
    if data_pagamento:
        data_pagamento = datetime.strptime(data_pagamento, '%Y-%m-%d').date()
    else:
        data_pagamento = date.today()
    
    pagamento_existente = Pagamento.query.filter_by(
        cliente_id=cliente.id,
        mes_referencia=mes_ref,
        ano_referencia=ano_ref
    ).first()
    
    if pagamento_existente:
        flash(
            f'⚠️ Já existe um pagamento registrado para {cliente.nome} '
            f'referente ao mês {mes_ref}/{ano_ref}. '
            f'Por favor, verifique o histórico de pagamentos deste cliente antes de registrar um novo pagamento.',
            'error'
        )
        referrer = request.referrer
        if referrer and 'inadimplentes' in referrer:
            return redirect(url_for('pagamentos.relatorio_inadimplentes'))
        else:
            return redirect(url_for('clientes.listar_clientes'))
    
    pagamento = Pagamento(
        cliente_id=cliente.id,
        valor_pago=valor_pago,
        data_pagamento=data_pagamento,
        mes_referencia=mes_ref,
        ano_referencia=ano_ref,
        observacoes=observacoes
    )
    
    db.session.add(pagamento)
    db.session.commit()
    
    flash(f'✅ Pagamento registrado para {cliente.nome} com sucesso!', 'success')
    
    referrer = request.referrer
    if referrer and 'inadimplentes' in referrer:
        return redirect(url_for('pagamentos.relatorio_inadimplentes'))
    else:
        return redirect(url_for('clientes.listar_clientes'))