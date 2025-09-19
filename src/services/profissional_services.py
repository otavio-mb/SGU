from ..models.profissional_model import ProfissionalModel
from ..entities.profissional import Profissional
from src import db


def cadastrar_profissional(profissional_entity):
    """Cadastra um novo profissional"""
    profissional_db = ProfissionalModel()
    profissional_db.nome = profissional_entity.nome
    
    db.session.add(profissional_db)
    db.session.commit()
    return profissional_db


def listar_profissionais():
    """Lista todos os profissionais"""
    profissionais_db = ProfissionalModel.query.all()
    profissionais_entities = [
        Profissional(p.nome) for p in profissionais_db
    ]
    return profissionais_entities


def listar_profissional_id(id):
    """Busca profissional por ID"""
    try:
        profissional_encontrado = ProfissionalModel.query.get(id)
        if profissional_encontrado:
            return Profissional(profissional_encontrado.nome)
    except Exception as e:
        print(f'Erro ao listar profissional por id: {e}')
        return None


def editar_profissional(id, profissional_entity):
    """Edita um profissional existente"""
    profissional_db = ProfissionalModel.query.get(id)
    
    if not profissional_db:
        return None
    
    profissional_db.nome = profissional_entity.nome
    db.session.commit()
    
    return Profissional(nome=profissional_db.nome)


def excluir_profissional(id):
    """Exclui um profissional"""
    profissional_db = ProfissionalModel.query.get(id)
    
    if profissional_db:
        # Verifica se há agendamentos vinculados
        from ..models.agendamento_model import AgendamentoModel
        agendamentos = AgendamentoModel.query.filter_by(
            id_profissional=id,
            status='agendado'
        ).first()
        
        if agendamentos:
            return {"erro": "Não é possível excluir profissional com agendamentos ativos"}
        
        db.session.delete(profissional_db)
        db.session.commit()
        return True
    
    return False