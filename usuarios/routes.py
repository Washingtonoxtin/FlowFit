from flask import Blueprint, render_template, redirect, url_for
from app.models import Cliente, Pagamento
from app.utils import login_required, calcular_status_cliente
from app.extensions import db
from datetime import date
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def dashboard():
    from app.utils import get_current_user
    usuario_atual = get_current_user()

    if not usuario_atual.is_admin():
        return redirect(url_for('clientes.listar_clientes'))

    hoje = date.today()
    meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
                7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
    nome_mes = meses_pt.get(hoje.month, 'Mês Desconhecido')

    clientes = Cliente.query.filter_by(ativo=True).all()
    total_clientes = len(clientes)
    clientes_pagos = []
    clientes_atrasados = []
    valor_total_esperado = 0

    for cliente in clientes:
        valor_total_esperado += cliente.valor_mensalidade

        status = calcular_status_cliente(cliente)

        if status == "Em dia":
            clientes_pagos.append(cliente)
        elif status == "Em atraso":
            meses_atraso, valor_devido = cliente.calcular_meses_atraso()
            clientes_atrasados.append({
                'cliente': cliente,
                'meses_atraso': meses_atraso,
                'valor_devido': valor_devido
            })

    valor_recebido = db.session.query(func.sum(Pagamento.valor_pago)).filter(
        Pagamento.mes_referencia == hoje.month,
        Pagamento.ano_referencia == hoje.year
    ).scalar() or 0

    stats = {
        'total_clientes': total_clientes,
        'clientes_pagos': len(clientes_pagos),
        'clientes_atrasados': len(clientes_atrasados),
        'valor_recebido': valor_recebido,
        'valor_esperado': valor_total_esperado,
        'valor_pendente': max(0, valor_total_esperado - valor_recebido),
        'percentual_pagos': round((len(clientes_pagos) / total_clientes * 100) if total_clientes > 0 else 0, 1)
    }

    return render_template('dashboard.html',
                           current_user=usuario_atual,
                           stats=stats,
                           hoje=hoje,
                           nome_mes=nome_mes,
                           clientes_atrasados=clientes_atrasados,
                           clientes_pagos=clientes_pagos)
