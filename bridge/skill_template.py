#!/usr/bin/env python3
"""
SKILL TEMPLATE - HARNESS v3.0
Meta-Protocolo: Como Criar uma Habilidade
"""

import os
import sys

def create_new_skill(skill_name, focus_area):
    """
    Protocolo de Criação de Habilidades:
    1. Pesquisa: Buscar as últimas tendências e melhores práticas na focus_area.
    2. Documentação: Gerar um README.md técnico com a arquitetura proposta.
    3. Implementação: Criar o código isolado em .venv usando uv.
    4. Validação: Criar testes unitários para a nova skill.
    """
    
    print(f"=== INICIANDO PROTOCOLO DE CRIAÇÃO: {skill_name} ===")
    
    # 1. PASSO DE PESQUISA (Simulado para o template)
    print(f"[*] Pesquisando últimas novidades para: {focus_area}...")
    
    # 2. PASSO DE DOCUMENTAÇÃO
    os.makedirs(f"agente-toolkit/skills/{skill_name}", exist_ok=True)
    with open(f"agente-toolkit/skills/{skill_name}/README.md", "w") as f:
        f.write(f"# Skill: {skill_name}\n\nArea: {focus_area}\n\nStatus: Draft\n\n## Arquitetura\n- [Insira aqui o resultado da pesquisa]")
    
    # 3. PASSO DE IMPLEMENTAÇÃO (A Lei do UV)
    print(f"[*] Inicializando ambiente isolado via UV em: agente-toolkit/skills/{skill_name}")
    # cmd = f"cd agente-toolkit/skills/{skill_name} && uv init && uv venv"
    
    print(f"=== PROTOCOLO FINALIZADO: {skill_name} PRONTA PARA IMPLEMENTAÇÃO ===")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        create_new_skill(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "General")
    else:
        print("Uso: python bridge/skill_template.py <nome_da_skill> <area_de_foco>")
