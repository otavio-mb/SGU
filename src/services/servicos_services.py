from ..models.servicos_model import ServicoModel
from ..entities.servico import Servico
from src import db


def cadastrar_servico(servico_entity):
    """Cadastra um novo serviço"""
    servico_db = ServicoModel()
    servico_db.descricao = servico_entity.descricao
    servico_db.valor = servico_entity.valor
    servico_db.horario_duracao = servico_entity.horario_duracao
    
    db.session.add(servico_db)
    db.session.commit()
    return servico_db


def listar_servicos():
    """Lista todos os serviços"""
    servicos_db = ServicoModel.query.all()
    servicos_entities = []
    
    for s in servicos_db:
        servico = Servico(
            descricao=s.descricao,
            valor=s.valor,
            horario_duracao=s.horario_duracao
        )
        servicos_entities.append(servico)
    
    return servicos_entities


def listar_servico_id(id):
    """Busca serviço por ID"""
    try:
        servico_encontrado = ServicoModel.query.get(id)
        if servico_encontrado:
            return Servico(
                descricao=servico_encontrado.descricao,
                valor=servico_encontrado.valor,
                horario_duracao=servico_encontrado.horario_duracao
            )
    except Exception as e:
        print(f'Erro ao listar serviço por id: {e}')
        return None


def editar_servico(id, servico_entity):
    """Edita um serviço existente"""
    servico_db = ServicoModel.query.get(id)
    
    if not servico_db:
        return None
    
    servico_db.descricao = servico_entity.descricao
    servico_db.valor = servico_entity.valor
    servico_db.horario_duracao = servico_entity.horario_duracao
    
    db.session.commit()
    
    return Servico(
        descricao=servico_db.descricao,
        valor=servico_db.valor,
        horario_duracao=servico_db.horario_duracao
    )


def excluir_servico(id):
    """Exclui um serviço"""
    servico_db = ServicoModel.query.get(id)
    
    if servico_db:
        # Verifica se há agendamentos vinculados
        from ..models.agendamento_model import AgendamentoModel
        agendamentos = AgendamentoModel.query.filter_by(
            id_servico=id,
            status='agendado'
        ).first()
        
        if agendamentos:
            return {"erro": "Não é possível excluir serviço com agendamentos ativos"}
        
        db.session.delete(servico_db)
        db.session.commit()
        return True
    
    return False


def buscar_servicos_por_valor(valor_min=None, valor_max=None):
    """Busca serviços por faixa de valor"""
    query = ServicoModel.query
    
    if valor_min:
        query = query.filter(ServicoModel.valor >= valor_min)
    
    if valor_max:
        query = query.filter(ServicoModel.valor <= valor_max)
    
    servicos_db = query.all()
    
    return [
        Servico(
            descricao=s.descricao,
            valor=s.valor,
            horario_duracao=s.horario_duracao
        ) for s in servicos_db
    ]